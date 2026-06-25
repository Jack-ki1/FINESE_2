import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
from io import StringIO

# Import centralized logging
logger = logging.getLogger(__name__)

# Import core components
from core.dataset_context import DatasetContext

# Import services
from services.cleaning_service import get_cleaning_suggestions, apply_cleaning_suggestions, suggest_optimal_type
from utils.data_utils import get_filtered_data, get_categorical_columns, get_numeric_columns
from config import BRAND_NAME, SECTION_HEADER_CLASS, SECTION_SUBHEADER_CLASS

# --- Constants (from types.py) ---
TYPE_CHOICES = [
    "int64", "float64", "object", "datetime64[ns]", "bool", "category",
    "string", "Int64", "Float64", "boolean"
]

TYPE_ICONS = {
    "int64": "🔢",
    "float64": "🧮",
    "object": "📄",
    "datetime64[ns]": "📅",
    "bool": "✅",
    "category": "🏷️",
    "string": "🔤",
    "Int64": "🔢?",
    "Float64": "🧮?",
    "boolean": "✅?"
}

TYPE_DESCRIPTIONS = {
    "int64": "Signed 64-bit integer (no nulls)",
    "Int64": "Nullable integer (supports NaN)",
    "float64": "Double-precision floating point",
    "Float64": "Nullable float (supports NaN)",
    "object": "Generic text or mixed types",
    "string": "Pandas string dtype (recommended for text)",
    "datetime64[ns]": "Timestamp with nanosecond precision",
    "bool": "True/False boolean (no nulls)",
    "boolean": "Nullable boolean (supports NaN)",
    "category": "Memory-efficient categorical encoding"
}

RISKY_CONVERSIONS = {
    ("object", "int64"): "⚠️ Converting text to integers may fail if non-numeric values exist",
    ("object", "float64"): "⚠️ Converting text to floats may fail if non-numeric values exist",
    ("object", "datetime64[ns]"): "⚠️ Converting text to dates may fail if invalid date formats exist",
    ("float64", "int64"): "⚠️ Converting floats to integers will truncate decimal parts",
    ("int64", "bool"): "⚠️ Converting integers to booleans treats 0 as False, others as True",
}


def render_missingness_analysis(df):
    """Add comprehensive missingness analysis functionality."""
    miss_cols = [c for c in df.columns if df[c].isnull().any()]
    if not miss_cols:
        st.success("✅ No missing values detected.")
        return
    
    st.markdown("### 🔍 Missingness Analysis")
    
    # Missingness correlation matrix
    miss_matrix = df[miss_cols].isnull().astype(int)
    miss_corr = miss_matrix.corr()
    
    with st.expander("Missingness Correlation Matrix", expanded=True):
        import plotly.express as px
        fig = px.imshow(
            miss_corr, 
            title="Missingness Correlation (Are columns missing together?)",
            text_auto=True,
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Classify each column
    st.markdown("### 📋 Missingness Pattern Classification")
    
    for col in miss_cols:
        miss_pct = df[col].isnull().mean() * 100
        
        # Check if missingness correlates with any other variable (MAR indicator)
        miss_indicator = df[col].isnull().astype(int)
        max_corr = 0
        correlated_with = None
        
        for other in get_numeric_columns(df):
            if other != col and df[other].notna().sum() > 10:
                try:
                    corr = abs(miss_indicator.corr(df[other]))
                    if corr > max_corr:
                        max_corr = corr
                        correlated_with = other
                except Exception:
                    pass
        
        if miss_pct > 60:
            pattern, advice = "MNAR likely", "Consider dropping or investigating data collection"
        elif max_corr > 0.3:
            pattern = f"MAR — related to `{correlated_with}`" 
            advice = "Use multiple imputation"
        else:
            pattern, advice = "MCAR likely", "Simple imputation (mean/median) acceptable"
        
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=f"`{col}`", value=f"{miss_pct:.1f}% missing")
            with col2:
                st.write(f"**Pattern:** {pattern}")
            with col3:
                st.write(f"**Advice:** {advice}")


def render_cleaning_tab(dataset_context: DatasetContext) -> None:
    """
    Unified Data Cleaning & Typing Tab.
    Combines Smart Cleanup + Intelligent Type Conversion in one workflow.
    """
    if dataset_context is None or dataset_context.filtered_df.empty:
        st.warning("⚠️ No working dataset found. Please load data first.")
        return

    wdf = dataset_context.filtered_df.copy()
    original_dtypes = wdf.dtypes.copy()

    st.markdown(f'<div class="{SECTION_HEADER_CLASS}">🧹 Unified Data Cleaning & Typing</div>', unsafe_allow_html=True)
    st.caption("Fix structural issues, standardize formats, and convert types — all in one place.")

    # --- Tab Navigation ---
    cleaning_tabs = st.tabs(["🤖 Smart Cleanup", "🔍 Missingness Analysis", "🔄 Type Converter", "📊 Summary"])

    # =============== TAB 1: Smart Cleanup ===============
    with cleaning_tabs[0]:
        _render_smart_cleanup_analysis(wdf)

    # =============== TAB 2: Missingness Analysis ===============
    with cleaning_tabs[1]:
        render_missingness_analysis(wdf)

    # =============== TAB 3: Type Converter ===============
    with cleaning_tabs[2]:
        _render_type_converter(wdf, original_dtypes)

    # =============== TAB 4: Summary & Audit ===============
    with cleaning_tabs[3]:
        _render_summary_tab()


# =============== SMART CLEANUP (from clean.py) ===============
def _render_smart_cleanup_analysis(wdf: pd.DataFrame) -> None:
    suggestions = _get_cached_cleaning_suggestions(wdf)

    if not suggestions:
        st.success("✅ No major cleanup issues detected. Your data looks clean!")
    else:
        st.info(f"🔍 Found {len(suggestions)} potential issues to address.")
        df_sug = pd.DataFrame([
            {"Column": s["column"], "Issue": s["issue"], "Recommendation": s["recommendation"], "Severity": s["severity"]}
            for s in suggestions
        ])
        st.dataframe(df_sug, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Preview All Fixes", type="primary", key="preview_fixes"):
                _apply_fixes_preview(wdf, suggestions)
        with col2:
            if st.button("🧹 Apply Fixes to Working Dataset", disabled=not st.session_state.get('preview_applied', False), key="apply_fixes"):
                _apply_fixes_to_session(wdf, suggestions)


def _generate_cleaning_suggestions(df: pd.DataFrame) -> List[dict]:
    suggestions = []
    missing = df.isnull().sum()
    high_miss = missing[missing > len(df) * 0.3]
    for col in high_miss.index:
        suggestions.append({
            "column": col,
            "issue": f"Missing values: {missing[col]} ({(missing[col]/len(df)*100):.1f}%)",
            "recommendation": "Drop column or impute with median/mean",
            "severity": "🔴 Critical"
        })

    for col in get_categorical_columns(df):
        cleaned = df[col].astype(str).str.replace(r'[^\d\.-]', '', regex=True)
        if cleaned.str.match(r'^-?\d*\.?\d*$').any():
            if not (df[col].nunique() / len(df) > 0.95):
                suggestions.append({
                    "column": col,
                    "issue": "Contains numeric characters but stored as text",
                    "recommendation": "Convert to numeric using `pd.to_numeric(..., errors='coerce')`",
                    "severity": "🟡 Medium"
                })

    for col in get_categorical_columns(df):
        original_nunique = df[col].nunique()
        normalized = df[col].astype(str).str.strip().str.lower()
        normalized_nunique = normalized.nunique()
        if normalized_nunique < original_nunique:
            diff = original_nunique - normalized_nunique
            suggestions.append({
                "column": col,
                "issue": f"{diff} inconsistent labels due to case/whitespace",
                "recommendation": "Normalize case and trim whitespace",
                "severity": "🟡 Low"
            })

    for col in get_numeric_columns(df):
        if (df[col] < 0).sum() > 0:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['price', 'cost', 'amount', 'fee', 'age', 'year']):
                suggestions.append({
                    "column": col,
                    "issue": f"{(df[col] < 0).sum()} negative values detected",
                    "recommendation": "Review for data entry errors (e.g., negative prices/ages)",
                    "severity": "🔴 Critical"
                })

    duplicates = df.columns[df.columns.duplicated()]
    if len(duplicates) > 0:
        dup_list = ', '.join(set(duplicates))
        suggestions.append({
            "column": "",
            "issue": f"Duplicate column names: {dup_list}",
            "recommendation": "Rename or remove duplicate columns to avoid ambiguity",
            "severity": "🔴 Critical"
        })

    zero_var = df.nunique() == 1
    if zero_var.any():
        cols = zero_var[zero_var].index.tolist()
        suggestions.append({
            "column": ", ".join(cols),
            "issue": "One or more columns have only one unique value",
            "recommendation": "Remove these columns — they add no predictive value",
            "severity": "🟡 Low"
        })

    for col in get_categorical_columns(df):
        sample = df[col].dropna().head(10).astype(str)
        date_patterns = [r'\d{4}-\d{1,2}-\d{1,2}', r'\d{1,2}/\d{1,2}/\d{4}', r'\d{1,2}-\d{1,2}-\d{4}']
        if any(sample.str.contains(p, na=False, regex=True).any() for p in date_patterns):
            suggestions.append({
                "column": col,
                "issue": "Looks like a date but stored as text",
                "recommendation": "Convert to datetime using `pd.to_datetime()`",
                "severity": "🟡 Medium"
            })

    return suggestions


@st.cache_data(show_spinner=False)
def _compute_cleaning_suggestions_cached(df_csv: str) -> List[dict]:
    """Compute cleaning suggestions from a CSV snapshot (cached by Streamlit).

    Reconstructs the DataFrame from the CSV string and delegates to
    _generate_cleaning_suggestions. Using CSV keeps the cache key deterministic.
    """
    try:
        df = pd.read_csv(StringIO(df_csv))
    except Exception:
        # If CSV parsing fails, return an empty suggestion list to fail gracefully
        return []
    return _generate_cleaning_suggestions(df)


def _apply_fixes_preview(df: pd.DataFrame, suggestions: List[dict]) -> None:
    try:
        tmp = df.copy()
        changes_log = []
        for suggestion in suggestions:
            col = suggestion["column"]
            rec = suggestion["recommendation"]
            if "Convert to numeric" in rec and col:
                tmp[col] = pd.to_numeric(tmp[col], errors='coerce')
                changes_log.append(f"✅ Converted `{col}` to numeric")
            elif "Normalize case" in rec and col:
                tmp[col] = tmp[col].astype(str).str.strip().str.lower()
                changes_log.append(f"✅ Normalized case & whitespace in `{col}`")
            elif "Drop column" in rec and col:
                tmp = tmp.drop(columns=[col])
                changes_log.append(f"❌ Dropped column `{col}`")
            elif "Convert to datetime" in rec and col:
                tmp[col] = pd.to_datetime(tmp[col], errors='coerce')
                changes_log.append(f"✅ Converted `{col}` to datetime")
        st.session_state['preview_applied'] = True
        st.session_state['cleaned_preview'] = tmp
        st.session_state['changes_log'] = changes_log
        st.success("✅ Preview generated!")
        with st.expander("📋 Changes Applied (Preview Only)"):
            for log in changes_log:
                st.write(f"- {log}")
        st.dataframe(tmp.head(10), use_container_width=True)
    except Exception as e:
        logger.error(f"Preview error: {e}")
        st.error(f"❌ Preview failed: {e}")


def _apply_fixes_to_session(df: pd.DataFrame, suggestions: List[dict]) -> None:
    if 'cleaned_preview' not in st.session_state:
        st.error("❌ No preview available. Click 'Preview All Fixes' first.")
        return
    try:
        st.session_state.work_df = st.session_state.cleaned_preview.copy()
        # Invalidate cached filtered view and health score after applying fixes
        st.session_state['filtered_data'] = None
        st.session_state['cached_data_health'] = None
        # Invalidate cleaning suggestions cache (Streamlit cached function)
        try:
            _compute_cleaning_suggestions_cached.clear()
        except Exception:
            pass
        del st.session_state['cleaned_preview']
        del st.session_state['preview_applied']
        if 'changes_log' in st.session_state:
            st.success("✅ Fixes applied to working dataset!")
            with st.expander("📄 Audit Trail"):
                for log in st.session_state.changes_log:
                    st.write(f"- {log}")
            del st.session_state['changes_log']
    except Exception as e:
        logger.error(f"Apply error: {e}")
        st.error(f"❌ Apply failed: {e}")


# =============== TYPE CONVERTER (from types.py) ===============
def _render_type_converter(wdf: pd.DataFrame, original_dtypes: pd.Series) -> None:
    with st.expander("⚙️ Advanced Options", expanded=False):
        auto_suggest = st.checkbox("✅ Auto-suggest types", value=True)
        show_sample = st.checkbox("👁️ Show sample values", value=True)
        show_risks = st.checkbox("🚨 Show conversion risks", value=True)

    if "type_selections" not in st.session_state:
        st.session_state.type_selections = {}

    changed_columns = []
    for col in wdf.columns:
        current_dtype = str(wdf[col].dtype)
        suggested_dtype = suggest_optimal_type(wdf[col], col) if auto_suggest else current_dtype
        default_index = TYPE_CHOICES.index(suggested_dtype) if suggested_dtype in TYPE_CHOICES else 2

        selected_dtype = st.selectbox(
            f"{col} · {TYPE_ICONS.get(current_dtype, '❓')} `{current_dtype}`",
            TYPE_CHOICES,
            index=default_index,
            key=f"type_{col}",
            help=TYPE_DESCRIPTIONS.get(suggested_dtype, "")
        )
        st.session_state.type_selections[col] = selected_dtype

        if show_risks:
            risk_key = (current_dtype, selected_dtype)
            if risk_key in RISKY_CONVERSIONS:
                st.warning(RISKY_CONVERSIONS[risk_key])

        if show_sample:
            sample_before = wdf[col].dropna().head(5).astype(str).tolist()
            sample_after = _try_convert_sample(wdf[col], selected_dtype).head(5).astype(str).tolist()
            c1, c2 = st.columns(2)
            with c1:
                st.caption("Before:")
                st.code("\n".join(sample_before[:5]), language="text")
            with c2:
                st.caption("After (preview):")
                st.code("\n".join(sample_after[:5]), language="text")

        if selected_dtype != current_dtype:
            changed_columns.append(col)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔍 Apply All Type Changes", type="primary", disabled=len(changed_columns) == 0, key="apply_types"):
            _apply_type_changes(wdf, original_dtypes, changed_columns)
    with col2:
        if st.button("↩️ Undo Type Changes", key="undo_types"):
            st.session_state.work_df = st.session_state.work_df.astype(original_dtypes)
            # Invalidate caches after undoing type changes
            st.session_state['filtered_data'] = None
            st.session_state['cached_data_health'] = None
            # Invalidate cleaning suggestions cache (Streamlit cached function)
            try:
                _compute_cleaning_suggestions_cached.clear()
            except Exception:
                pass
            st.success("🔁 Types reverted.")
            st.rerun()
    with col3:
        if st.button("📥 Export Type Log", key="export_type_log"):
            markdown = _export_conversion_log_as_markdown(st.session_state.get("conversion_log", []), original_dtypes)
            st.download_button(
                label="⬇️ Download as Markdown (.md)",
                data=markdown,
                file_name=f"{BRAND_NAME.lower()}_type_conversion_log_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                key="download_type_log_cleaning"
            )

    if changed_columns:
        st.info(f"💡 {len(changed_columns)} type(s) modified. Click **Apply** to commit.")
    else:
        st.success("✅ All columns are correctly typed.")


def _apply_type_changes(wdf: pd.DataFrame, original_dtypes: pd.Series, changed_columns: List[str]) -> None:
    success_count = 0
    failure_count = 0
    log_entries = []
    wdf_converted = wdf.copy()

    for col in wdf.columns:
        target_dtype = st.session_state.type_selections[col]
        current_dtype = str(wdf[col].dtype)
        if target_dtype == current_dtype:
            continue

        try:
            wdf_converted[col] = safe_convert_type(wdf_converted[col], target_dtype)
            success_count += 1
            log_entries.append(f"✅ `{col}`: `{current_dtype}` → `{target_dtype}`")
        except Exception as e:
            failure_count += 1
            log_entries.append(f"❌ `{col}`: Failed ({e})")
            st.warning(f"⚠️ Failed to convert `{col}`: {str(e)}")

    if failure_count == 0:
        st.session_state.work_df = wdf_converted
        # Invalidate caches after changing working dataset types
        st.session_state['filtered_data'] = None
        st.session_state['cached_data_health'] = None
        # Invalidate cleaning suggestions cache (Streamlit cached function)
        try:
            _compute_cleaning_suggestions_cached.clear()
        except Exception:
            pass
        st.session_state.conversion_log = log_entries
        st.success(f"✅ Successfully converted {success_count} column(s).")
    else:
        st.warning(f"⚠️ Converted {success_count} column(s) with {failure_count} failure(s). Check warnings above.")


# The _suggest_optimal_type function has been removed since we're now using
# the suggest_optimal_type function from the cleaning_service


def _try_convert_sample(series: pd.Series, target_type: str) -> pd.Series:
    """Try to convert a sample of the series to target type for preview."""
    try:
        if target_type == "datetime64[ns]":
            return pd.to_datetime(series.head(5), errors="coerce")
        elif target_type in ["Int64", "Float64"]:
            return pd.to_numeric(series.head(5), errors="coerce").astype(target_type)
        else:
            return series.head(5).astype(target_type, errors="ignore")
    except Exception:
        return series.head(5)


def _export_conversion_log_as_markdown(log_entries: List[str], original_dtypes: pd.Series) -> str:
    """Export type conversion log as markdown."""
    md = f"# {BRAND_NAME} Type Conversion Log\n\n"
    md += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "## Original Data Types\n\n"
    for col, dtype in original_dtypes.items():
        md += f"- `{col}`: `{dtype}`\n"
    md += "\n## Conversion Actions\n\n"
    for entry in log_entries:
        md += f"{entry}\n"
    return md


def _render_summary_tab() -> None:
    """Render the summary and audit tab."""
    st.markdown("### 📊 Data Type Summary")
    
    if "work_df" not in st.session_state or st.session_state.work_df is None or st.session_state.work_df.empty:
        st.info("No data available.")
        return
        
    df = st.session_state.work_df
    type_counts = df.dtypes.value_counts()
    
    # Display type distribution
    st.write("**Current Data Types Distribution:**")
    for dtype, count in type_counts.items():
        st.write(f"- `{dtype}`: {count} column(s)")
        
    # Show conversion log if exists
    if "conversion_log" in st.session_state and st.session_state.conversion_log:
        st.markdown("### 📜 Conversion History")
        with st.expander("View Full Conversion Log"):
            for log_entry in st.session_state.conversion_log:
                st.write(log_entry)
    else:
        st.info("No type conversions have been applied yet.")


def _df_fingerprint(df: pd.DataFrame) -> str:
    """Create a small fingerprint for a DataFrame to use as a cache key."""
    try:
        cols = tuple(df.columns.tolist())
        dtypes = tuple(str(t) for t in df.dtypes.tolist())
        shape = (df.shape[0], df.shape[1])
        # Use total null count as a cheap changing metric
        nulls = int(df.isnull().sum().sum())
        key = (shape, cols, dtypes, nulls)
        return str(key)
    except Exception:
        # Fallback to length-based fingerprint if something unexpected happens
        return f"fp_{len(df)}_{df.shape[1]}"


def _get_cached_cleaning_suggestions(df: pd.DataFrame) -> List[dict]:
    """Return cleaning suggestions using Streamlit's @st.cache_data for persistence.

    We serialize the DataFrame to CSV and use that string as the cache key. This is
    robust and ensures cache entries are invalidated when the DataFrame changes.
    """
    if df is None:
        return []

    try:
        # Serialize a stable snapshot of the dataframe for hashing by st.cache_data
        df_csv = df.to_csv(index=False)
    except Exception:
        # Fallback: use a fingerprint if serialization fails
        df_csv = _df_fingerprint(df)

    return _compute_cleaning_suggestions_cached(df_csv)

