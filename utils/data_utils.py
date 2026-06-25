import pandas as pd
import streamlit as st
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)


def is_numeric_column(series: pd.Series) -> bool:
    """Check if a series contains numeric data."""
    if pd.api.types.is_numeric_dtype(series):
        return True
    
    # Try to convert to numeric and see if it succeeds
    try:
        pd.to_numeric(series.dropna())
        return True
    except (ValueError, TypeError):
        return False


def is_categorical_column(series: pd.Series) -> bool:
    """Check if a series contains categorical data."""
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series):
        return True
    
    # If it's not object or category but has few unique values, consider it categorical
    if series.nunique() / len(series) < 0.05:  # Less than 5% unique values
        return True
    
    return False


def is_datetime_column(series: pd.Series) -> bool:
    """Check if a series contains datetime data."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    
    # Try to convert to datetime and see if it succeeds
    try:
        pd.to_datetime(series.dropna().head(10), errors='raise', infer_datetime_format=True)
        return True
    except (ValueError, TypeError):
        return False


def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Get list of numeric columns in DataFrame."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Get list of categorical columns in DataFrame."""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

def get_datetime_columns(df: pd.DataFrame) -> List[str]:
    """Get list of datetime columns in DataFrame."""
    datetime_cols = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            datetime_cols.append(col)
        else:
            # Try to parse as datetime
            try:
                pd.to_datetime(df[col], errors='raise', infer_datetime_format=True)
                datetime_cols.append(col)
            except:
                continue
    return datetime_cols

def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame dtypes to save memory on upload."""
    df_optimized = df.copy()
    
    for col in df_optimized.select_dtypes('int64').columns:
        df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='integer')
    
    for col in df_optimized.select_dtypes('float64').columns:
        df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='float')
    
    for col in df_optimized.select_dtypes('object').columns:
        if df_optimized[col].nunique() / len(df_optimized) < 0.5:
            df_optimized[col] = df_optimized[col].astype('category')
    
    return df_optimized


def safe_convert_type(series: pd.Series, target_type: str) -> pd.Series:
    """Safely convert a series to target_type.

    This function must return ONLY a Series because callers assign the result
    directly into a DataFrame column.
    """
    try:
        if target_type == 'int64':
            return pd.to_numeric(series, errors='coerce').fillna(0).astype('int64')
        if target_type == 'float64':
            return pd.to_numeric(series, errors='coerce').astype('float64')
        if target_type == 'datetime64[ns]':
            return pd.to_datetime(series, errors='coerce')
        if target_type == 'bool':
            mapping = {'true': True, 'false': False, 'yes': True, 'no': False,
                       '1': True, '0': False, 't': True, 'f': False}
            return series.astype(str).str.lower().map(mapping).astype('boolean')
        if target_type == 'object':
            return series.astype('object')
        # Fallback: rely on pandas astype
        return series.astype(target_type)
    except Exception as e:
        logger.warning(f"Type conversion failed for {target_type}: {e}")
        return series


def get_filtered_data() -> pd.DataFrame:
    """
    Apply global user-defined filters to the working dataset (`work_df`).
    Filters include:
      - Date range (auto-detected date columns)
      - Categorical selection (dropdowns for low-cardinality columns)
      - Numeric range sliders (for top 10 numeric columns)

    Returns:
        pd.DataFrame: Filtered view of `st.session_state.work_df`
    """
    if "work_df" not in st.session_state or st.session_state.work_df is None or st.session_state.work_df.empty:
        return pd.DataFrame()

    # Lightweight caching: avoid recomputing filtered view on every render
    try:
        work = st.session_state.work_df
        # Create a fingerprint based on key properties of the dataframe
        fkey = (
            len(work),
            work.shape[1],
            hash(str(sorted(work.columns.tolist()))),  # Include column names in fingerprint
            int(work.memory_usage(deep=True).sum()) if work.shape[0] > 0 else 0
        )
        cached = st.session_state.get('filtered_data')
        cached_key = st.session_state.get('filtered_data_key')
        if cached is not None and cached_key == fkey:
            return cached.copy()
    except Exception as e:
        # if anything goes wrong with fingerprinting, fall through and recompute
        logger.warning(f"Caching failed, falling back to recomputation: {e}")
        pass

    # Work with a copy to avoid modifying the original
    filtered = st.session_state.work_df.copy()

    # Limit the size of data we work with to prevent memory issues
    max_rows = 10000  # Limit to 10k rows for performance
    if len(filtered) > max_rows:
        st.info(f"📊 Filtering applied to full dataset of {len(filtered):,} rows (sampling shown below for performance)")
        # Note: We'll apply filters to the full dataset, but display sample for UI
    else:
        max_rows = len(filtered)

    # --- DATE RANGE FILTER ---
    date_candidates = [
        c for c in filtered.columns
        if "date" in c.lower() or "time" in c.lower() or pd.api.types.is_datetime64_any_dtype(filtered[c])
    ]

    if date_candidates:
        # Initialize selected date column if not set
        if "selected_date_col" not in st.session_state:
            st.session_state.selected_date_col = date_candidates[0]

        dcol = st.session_state.selected_date_col

        try:
            filtered[dcol] = pd.to_datetime(filtered[dcol], errors="coerce")
            valid_dates = filtered[dcol].dropna()
            if len(valid_dates) > 0:
                mind, maxd = valid_dates.min(), valid_dates.max()
                if pd.notna(mind) and pd.notna(maxd):
                    # Initialize date range if not set
                    if "date_range" not in st.session_state:
                        st.session_state.date_range = (mind.date(), maxd.date())

                    sel = st.session_state.date_range
                    if isinstance(sel, tuple) and len(sel) == 2:
                        try:
                            s = pd.to_datetime(sel[0])
                            e = pd.to_datetime(sel[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                            filtered = filtered[(filtered[dcol] >= s) & (filtered[dcol] <= e)]
                        except Exception as e:
                            logger.warning(f"Invalid date range: {e}")
        except Exception as e:
                            logger.warning(f"Failed to parse date column '{dcol}': {e}")

    # --- CATEGORICAL FILTERS ---
    cat_cols = filtered.select_dtypes(include=["object", "category"]).columns.tolist()

    for c in cat_cols:
        n_unique = filtered[c].nunique(dropna=False)
        if 1 < n_unique <= 30:  # Reasonable cardinality for dropdown
            key = f"filter_{c}"
            unique_vals = filtered[c].astype(str).unique().tolist()
            default_selection = unique_vals  # Default: all selected

            # Initialize session state if needed
            if key not in st.session_state:
                st.session_state[key] = default_selection

            picked = st.session_state[key]
            if isinstance(picked, list) and len(picked) > 0:
                filtered = filtered[filtered[c].astype(str).isin(picked)]

    # --- NUMERIC SLIDERS ---
    num_cols = filtered.select_dtypes(include=[np.number]).columns.tolist()
    num_cols = num_cols[:10]  # Cap at 10 to avoid clutter

    for c in num_cols:
        min_val = float(filtered[c].min())
        max_val = float(filtered[c].max())

        if min_val == max_val:
            continue

        key = f"slider_{c}"

        if key not in st.session_state:
            st.session_state[key] = (min_val, max_val)

        lo, hi = st.session_state[key]
        lo = max(lo, min_val)
        hi = min(hi, max_val)
        filtered = filtered[(filtered[c] >= lo) & (filtered[c] <= hi)]

    # Store filtered copy in session state for quick reuse
    try:
        st.session_state['filtered_data'] = filtered.copy()
        st.session_state['filtered_data_key'] = fkey
    except Exception:
        pass

    return filtered