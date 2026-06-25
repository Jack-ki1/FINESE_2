import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Import centralized logging
logger = logging.getLogger(__name__)

# Import core components
from core.dataset_context import DatasetContext

# Import services
from services.health_service import calculate_data_health_score, generate_health_insights
from services.chart_service import (
    create_completeness_chart, 
    create_missing_heatmap, 
    create_outlier_analysis, 
    create_correlation_heatmap, 
    create_distribution_plots,
    MAX_ROWS_FOR_PLOT
)
from utils.ui_utils import render_section_header, render_section_subheader, card, card_container

# --- GLOBAL BADGE MAP (Single Source of Truth) ---
BADGE_MAP = {
    95: "🏆 Perfect Dataset",
    90: "🥇 Data Master",
    80: "🥈 Clean Data Apprentice",
    70: "🥉 Data Novice",
    60: "⚠️ Needs Attention",
    0: "📉 Critical Issues"
}


def render_review_tab(dataset_context: DatasetContext) -> None:
    """
    Unified Data Review Tab: Combines Overview + Quality into a single intelligent workflow.
    """
    if dataset_context is None or dataset_context.filtered_df.empty:
        st.warning("⚠️ No data available. Please load or filter data first.")
        return

    filtered = dataset_context.filtered_df

    # --- Section 1: Data Preview (from overview.py) ---
    with card("📊 Data Snapshot"):
        render_section_subheader("First & last 10 rows")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 10 Rows")
            st.dataframe(filtered.head(10), use_container_width=True)
        with col2:
            st.subheader("Bottom 10 Rows")
            st.dataframe(filtered.tail(10), use_container_width=True)

    # --- Section 2: Column Summary (from overview.py) ---
    st.markdown('<hr class="div" />', unsafe_allow_html=True)
    with card("📋 Column Summary"):
        try:
            miss = filtered.isnull().sum()
            pct_missing = (miss / len(filtered) * 100).round(2)
            n_unique = filtered.nunique(dropna=False)

            meta_df = pd.DataFrame({
                "Column": filtered.columns,
                "Dtype": filtered.dtypes.astype(str),
                "Missing": miss.values,
                "% Missing": pct_missing.values,
                "Unique Values": n_unique.values
            })
            st.dataframe(meta_df, use_container_width=True, hide_index=True)

            with st.expander("🔍 Raw DataFrame.info()"):
                buf = StringIO()
                filtered.info(buf=buf)
                st.text(buf.getvalue())
        except Exception as e:
            logger.error(f"Error generating column summary: {e}")
            st.error("❌ Failed to generate column summary.")

    # --- Section 3: Auto-Summary Engine + Recommendations (split cards) ---
    st.markdown('<hr class="div" />', unsafe_allow_html=True)
    st.markdown("")

    split_a, split_b = st.columns(2)
    with split_a:
        with card("🧠 Auto-Summary Engine"):
            st.caption("AI-driven insights to detect hidden data issues")
            if st.button("📄 Generate Data DNA Report", type="primary"):
                with st.spinner("Analyzing your data..."):
                    insights = generate_health_insights(filtered)

                st.markdown("### 🧬 Data DNA Report")
                if not insights:
                    st.success("✅ No critical issues detected. Your data looks clean!")
                else:
                    for insight in insights:
                        st.markdown(f"- {insight}")

    with split_b:
        with card("📊 Recommendations"):
            st.caption("Suggested cleanup steps")
            with st.expander("📌 View Suggested Next Steps", expanded=False):
                st.markdown("""
                - 🔧 Use **Clean → Fill Mode** on columns with >30% missing values  
                - 🔄 Use **Types → Convert** to fix inconsistent strings (e.g., currency, commas)  
                - 📉 Use **Review → Outlier Analysis** to investigate skewed distributions  
                """)

    # --- Section 4: Data Health Scorecard (from quality.py) ---
    st.markdown('<hr class="div" />', unsafe_allow_html=True)
    with card("🎯 Data Quality Dashboard"):
        st.caption("Comprehensive assessment of completeness, consistency, accuracy, and reliability")
        scorecard = calculate_data_health_score(filtered)
        _render_scorecard(scorecard)

    # --- Section 5: Visual Diagnostics (from quality.py) ---
    tabs = st.tabs([
        "🔍 Completeness",
        "🟨 Missing Heatmap",
        "📉 Outliers",
        "🌡️ Correlation",
        "📈 Distributions"
    ])

    with tabs[0]:
        with card("Diagnostics: Completeness"):
            # Enforce MAX_ROWS_FOR_PLOT constraint
            if len(filtered) > MAX_ROWS_FOR_PLOT:
                st.warning(f"Dataset has {len(filtered)} rows, which exceeds the limit of {MAX_ROWS_FOR_PLOT} for plotting. Showing downscaled version.")
                sample_df = filtered.sample(n=MAX_ROWS_FOR_PLOT, random_state=42)
                fig = create_completeness_chart(sample_df)
            else:
                fig = create_completeness_chart(filtered)
            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    with tabs[1]:
        with card("Diagnostics: Missing Heatmap"):
            # Downsample for performance
            if len(filtered) > MAX_ROWS_FOR_PLOT or len(filtered.columns) > 20:
                sample_size = min(MAX_ROWS_FOR_PLOT, len(filtered))
                col_limit = min(20, len(filtered.columns))
                sample_df = filtered.iloc[:, :col_limit].sample(n=sample_size, random_state=42)
                st.warning(f"Showing a sample of the data for performance: {sample_size} rows × {col_limit} columns")
                fig = create_missing_heatmap(sample_df)
            else:
                fig = create_missing_heatmap(filtered)
            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    with tabs[2]:
        with card("Diagnostics: Outliers"):
            _render_outlier_analysis(filtered)

    with tabs[3]:
        with card("Diagnostics: Correlation"):
            # Downsample for performance
            if len(filtered) > MAX_ROWS_FOR_PLOT or len(filtered.select_dtypes(include=[np.number]).columns) > 20:
                sample_size = min(MAX_ROWS_FOR_PLOT, len(filtered))
                sample_df = filtered.sample(n=sample_size, random_state=42)
                st.warning(f"Showing a sample of the data for performance: {sample_size} rows")
                fig = create_correlation_heatmap(sample_df)
            else:
                fig = create_correlation_heatmap(filtered)
            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    with tabs[4]:
        with card("Diagnostics: Distributions"):
            # Downsample for performance
            if len(filtered) > MAX_ROWS_FOR_PLOT:
                sample_size = min(MAX_ROWS_FOR_PLOT, len(filtered))
                sample_df = filtered.sample(n=sample_size, random_state=42)
                st.warning(f"Showing a sample of the data for performance: {sample_size} rows")
                figures = create_distribution_plots(sample_df)
            else:
                figures = create_distribution_plots(filtered)
            
            for fig in figures:
                st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    # --- Section 6: YData Profiling Integration (final card) ---
    st.markdown('<hr class="div" />', unsafe_allow_html=True)
    with card("🔬 Full YData Profile"):
        # Add guardrails for ydata-profiling
        if len(filtered) > 5000:
            st.warning(f"Dataset has {len(filtered)} rows, which may cause performance issues. Recommended to use with < 5000 rows.")
        
        if st.button("🔬 Generate Full YData Profile", type="secondary"):
            try:
                # Lazy import for ydata-profiling
                from ydata_profiling import ProfileReport
                with st.spinner("Generating comprehensive data profile..."):
                    try:
                        # Create profile report with limits
                        profile = ProfileReport(
                            filtered.head(5000),  # Limit to first 5000 rows
                            title="FINESE - Comprehensive Data Profile",
                            pool_size=0  # Disable multiprocessing to avoid issues in some environments
                        )
                        # Convert to HTML string
                        profile_html = profile.to_html()

                        # Display using components
                        st.markdown("### Generated Profile Report")
                        st.components.v1.html(profile_html, height=800, scrolling=True)

                        # Also provide download option
                        st.download_button(
                            label="📥 Download Full Profile Report",
                            data=profile_html,
                            file_name="ydata_profile_report.html",
                            mime="text/html"
                        )
                    except Exception as e:
                        st.error(f"❌ Error generating profile: {e}")
                        logger.exception("Profile generation error")
            except ImportError:
                st.error("❌ ydata-profiling is not installed. Run: `pip install ydata-profiling`")
                st.info("💡 You can install it with: `pip install ydata-profiling`")


def _render_scorecard(scorecard: Dict) -> None:
    score = scorecard["final_score"]
    badge = next((v for k, v in BADGE_MAP.items() if score >= k), BADGE_MAP[0])
    st.markdown(f"""
    <div style="text-align:center; padding:20px; background:#f0f7ff; border-radius:12px; margin:20px 0;">
        <h2>📊 DATA HEALTH SCORE: <span style="font-size:2em; color:#0ea5a4;">{score}/100</span></h2>
        <p style="font-size:1.2em; color:#1f2937;">🎯 {badge}</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    metrics = [
        ("Completeness", scorecard["details"]["completeness"], "🟢 Good" if scorecard["details"]["completeness"] >= 90 else "🟡 Warning"),
        ("Consistency", scorecard["details"]["consistency"], "🟢 Good" if scorecard["details"]["consistency"] >= 90 else "🟡 Warning"),
        ("Accuracy", scorecard["details"]["accuracy"], "🟢 Good" if scorecard["details"]["accuracy"] >= 80 else "🟡 Warning"),
        ("Uniqueness", scorecard["details"]["uniqueness"], "🟢 Good" if scorecard["details"]["uniqueness"] >= 90 else "🟡 Warning"),
        ("Timeliness", scorecard["details"]["timeliness"], "🟢 Good" if scorecard["details"]["timeliness"] >= 80 else "🟡 Warning"),
    ]
    for i, (label, value, status) in enumerate(metrics):
        with cols[i]:
            st.metric(label=label, value=f"{value}%", delta=status)


def _render_outlier_analysis(df: pd.DataFrame) -> None:
    # Import from utils instead of checking data types directly
    from utils.data_utils import is_numeric_column
    numeric_cols = [col for col in df.columns if is_numeric_column(df[col])]
    
    if not numeric_cols:
        st.info("No numeric columns available for outlier analysis.")
        return
    selected_col = st.selectbox("Select column for outlier analysis", numeric_cols, key="outlier_col_select")
    try:
        # Downsample for performance if needed
        if len(df) > MAX_ROWS_FOR_PLOT:
            sample_df = df.sample(n=MAX_ROWS_FOR_PLOT, random_state=42)
            st.warning(f"Analyzing a sample of {MAX_ROWS_FOR_PLOT} rows for performance")
        else:
            sample_df = df
            
        outlier_stats, fig = create_outlier_analysis(sample_df, selected_col)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"#### Outlier Stats: `{selected_col}`")
            st.write(f"Lower Bound: `{outlier_stats['lower_bound']:.2f}`")
            st.write(f"Upper Bound: `{outlier_stats['upper_bound']:.2f}`")
            st.write(f"Outliers: `{outlier_stats['outlier_count']:,}` ({outlier_stats['outlier_percentage']:.1f}%)")
            if outlier_stats['outlier_count'] > 0:
                st.warning("⚠️ Consider investigating or cleaning these outliers.")
        with col2:
            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
    except Exception as e:
        logger.error(f"Outlier analysis failed on {selected_col}: {e}")
        st.error(f"❌ Could not compute outliers for `{selected_col}`")