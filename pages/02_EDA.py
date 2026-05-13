"""
🔍 EDA - Exploratory Data Analysis
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
st.set_page_config(page_title="EDA | FINESE2", page_icon="🔍", layout="wide")

from utils.session_state import SessionManager
from utils.styling import render_section_header, render_status_badge, render_metric_card
from modules.eda_engine import EDAEngine
from modules.ai_assistant import render_ai_settings_sidebar

SessionManager.init()


# Set current page in session state
st.session_state.current_page = "02_EDA.py"

st.title("🔍 Exploratory Data Analysis")

if not SessionManager.has_data():
    st.warning("⚠️ No data loaded. Please load data in the Data section first.")
    st.stop()

df = SessionManager.get_df()


# Quick Profile
render_section_header("Quick Profile", "Automated data profiling and quality assessment")

profile = EDAEngine.quick_profile(df)
issues = EDAEngine.detect_issues(df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_metric_card("Rows", f"{profile['shape'][0]:,}", "Total records", "📊")
with col2:
    render_metric_card("Columns", profile['shape'][1], "Total features", "📈")
with col3:
    render_metric_card("Memory", f"{profile['memory_usage'] / 1024 / 1024:.1f} MB", "Dataset size", "💾")
with col4:
    render_metric_card("Duplicates", issues['duplicates'], "Identical rows", "🚫")

# Issues Panel
if any([issues['missing_high'], issues['missing_medium'], issues['constant_columns'], 
        issues['high_cardinality'], issues['outliers'], issues['skewed']]):
    with st.expander("⚠️ Data Quality Issues Detected", expanded=True):
        cols = st.columns(3)

        with cols[0]:
            if issues['missing_high']:
                st.markdown("**High Missing (>50%)**")
                for item in issues['missing_high']:
                    st.markdown(f"<span class='status-error'>• {item['column']}: {item['issue']}</span>", unsafe_allow_html=True)
            if issues['missing_medium']:
                st.markdown("**Medium Missing (10-50%)**")
                for item in issues['missing_medium']:
                    st.markdown(f"<span class='status-warning'>• {item['column']}: {item['issue']}</span>", unsafe_allow_html=True)

        with cols[1]:
            if issues['constant_columns']:
                st.markdown("**Constant Columns**")
                for col in issues['constant_columns']:
                    st.markdown(f"<span class='status-warning'>• {col}</span>", unsafe_allow_html=True)
            if issues['high_cardinality']:
                st.markdown("**High Cardinality**")
                for item in issues['high_cardinality']:
                    st.markdown(f"<span class='status-info'>• {item['column']}: {item['unique']} unique</span>", unsafe_allow_html=True)

        with cols[2]:
            if issues['outliers']:
                st.markdown("**Outliers Detected**")
                for col, count in list(issues['outliers'].items())[:5]:
                    st.markdown(f"<span class='status-warning'>• {col}: {count} outliers</span>", unsafe_allow_html=True)
            if issues['skewed']:
                st.markdown("**Skewed Distributions**")
                for item in issues['skewed'][:5]:
                    st.markdown(f"<span class='status-info'>• {item['column']}: skew={item['skewness']:.2f}</span>", unsafe_allow_html=True)

# Tabs for different EDA views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📈 Distributions", "🔗 Correlations", "❓ Missing Values", "📑 Full Report"])

with tab1:
    render_section_header("Statistical Overview", "")

    numeric_cols = list(profile['numeric_summary'].keys())
    if numeric_cols:
        overview_data = []
        for col in numeric_cols:
            stats = profile['numeric_summary'][col]
            overview_data.append({
                'Column': col,
                'Mean': f"{stats['mean']:.4f}",
                'Median': f"{stats['median']:.4f}",
                'Std': f"{stats['std']:.4f}",
                'Min': f"{stats['min']:.4f}",
                'Max': f"{stats['max']:.4f}",
                'Skew': f"{stats['skewness']:.4f}",
                'IQR': f"{stats['iqr']:.4f}"
            })
        st.dataframe(pd.DataFrame(overview_data), use_container_width=True, hide_index=True)

    cat_cols = list(profile['categorical_summary'].keys())
    if cat_cols:
        st.subheader("Categorical Summary")
        cat_data = []
        for col in cat_cols:
            stats = profile['categorical_summary'][col]
            top_vals = list(stats['top_values'].keys())[:3]
            cat_data.append({
                'Column': col,
                'Unique': stats['unique'],
                'Top Values': ', '.join(top_vals),
                'Top %': f"{stats['top_pct']:.1f}%"
            })
        st.dataframe(pd.DataFrame(cat_data), use_container_width=True, hide_index=True)

with tab2:
    render_section_header("Distribution Analysis", "")

    all_cols = df.columns.tolist()
    selected_col = st.selectbox("Select column to analyze", all_cols)

    if selected_col:
        fig = EDAEngine.create_distribution_plot(df, selected_col)
        st.plotly_chart(fig, use_container_width=True)

        if selected_col in profile['numeric_summary']:
            stats = profile['numeric_summary'][selected_col]
            cols = st.columns(4)
            cols[0].metric("Mean", f"{stats['mean']:.4f}")
            cols[1].metric("Median", f"{stats['median']:.4f}")
            cols[2].metric("Skewness", f"{stats['skewness']:.4f}")
            cols[3].metric("Kurtosis", f"{stats['kurtosis']:.4f}")

with tab3:
    render_section_header("Correlation Analysis", "")

    numeric_df = df.select_dtypes(include=[np.number])
    if len(numeric_df.columns) >= 2:
        fig = EDAEngine.create_correlation_heatmap(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        if profile['correlations']['high_pairs']:
            st.subheader("Strong Correlations")
            corr_df = pd.DataFrame(profile['correlations']['high_pairs'])
            st.dataframe(corr_df, use_container_width=True, hide_index=True)
    else:
        st.info("Need at least 2 numeric columns for correlation analysis.")

with tab4:
    render_section_header("Missing Values Pattern", "")

    fig = EDAEngine.create_missing_heatmap(df)
    st.plotly_chart(fig, use_container_width=True)

    missing_summary = pd.DataFrame({
        'Column': df.columns,
        'Missing Count': df.isnull().sum().values,
        'Missing %': (df.isnull().mean().values * 100).round(2)
    })
    missing_summary = missing_summary[missing_summary['Missing Count'] > 0].sort_values('Missing %', ascending=False)

    if not missing_summary.empty:
        st.dataframe(missing_summary, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No missing values found!")

with tab5:
    render_section_header("Full Profiling Report", "Generate comprehensive HTML report")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Generate ydata-profiling Report", type="primary", use_container_width=True):
            with st.spinner("Generating report... This may take a moment."):
                html_report = EDAEngine.generate_ydata_report(df)
                if html_report:
                    SessionManager.set("eda_html", html_report)
                    st.success("Report generated!")
                    st.download_button("⬇️ Download HTML Report", html_report.encode(), 
                                     "eda_report.html", "text/html", use_container_width=True)
                else:
                    st.error("Could not generate ydata-profiling report. Make sure ydata-profiling is installed.")

    with col2:
        if st.button("📊 Generate Sweetviz Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                html_report = EDAEngine.generate_sweetviz_report(df)
                if html_report:
                    st.download_button("⬇️ Download Sweetviz Report", html_report.encode(),
                                     "sweetviz_report.html", "text/html", use_container_width=True)
                else:
                    st.error("Could not generate Sweetviz report. Make sure sweetviz is installed.")

    # Show cached report if available
    cached_report = SessionManager.get("eda_html")
    if cached_report:
        st.markdown("### Cached Report Preview")
        st.components.v1.html(cached_report, height=800, scrolling=True)

# Data Relationships Explorer
with st.expander("🔗 Data Relationships Explorer", expanded=False):
    render_section_header("Relationships Explorer", "Discover correlations and associations in your data")
    
    # Identify numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(numeric_cols) >= 2:
        st.subheader("Numeric Relationships")
        
        # Correlation matrix with different methods
        col1, col2 = st.columns(2)
        with col1:
            corr_method = st.selectbox("Correlation Method", ["pearson", "spearman", "kendall"], key="rel_corr_method")
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr(method=corr_method)
        
        # Create correlation heatmap
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdBu',
            title=f"{corr_method.title()} Correlation Matrix",
            labels=dict(color="Correlation")
        )
        
        fig.update_xaxes(side="top")
        st.plotly_chart(fig, use_container_width=True)
        
        # Strong correlations table
        strong_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                val = corr_matrix.iloc[i, j]
                if abs(val) > 0.5:  # Threshold for strong correlation
                    strong_corrs.append({
                        'Variable 1': corr_matrix.columns[i],
                        'Variable 2': corr_matrix.columns[j],
                        'Correlation': round(val, 3)
                    })
        
        if strong_corrs:
            st.subheader("Strong Correlations (|r| > 0.5)")
            st.dataframe(pd.DataFrame(strong_corrs), use_container_width=True)
        else:
            st.info("No strong correlations found (|r| > 0.5)")
    
    if len(cat_cols) >= 2:
        st.subheader("Categorical Relationships")
        
        # Select two categorical variables for association analysis
        col1, col2 = st.columns(2)
        with col1:
            cat_var1 = st.selectbox("First Categorical Variable", cat_cols, key="cat_var1")
        with col2:
            cat_var2 = st.selectbox("Second Categorical Variable", [c for c in cat_cols if c != cat_var1], key="cat_var2")
        
        if st.button("🔍 Analyze Association", key="analyze_assoc"):
            # Create cross-tabulation
            crosstab = pd.crosstab(df[cat_var1], df[cat_var2], margins=True)
            st.dataframe(crosstab, use_container_width=True)
            
            # Create mosaic plot using bar charts
            df_mosaic = df[[cat_var1, cat_var2]].value_counts().reset_index()
            df_mosaic.columns = [cat_var1, cat_var2, 'Count']
            
            fig = px.bar(
                df_mosaic, 
                x=cat_var1, 
                y='Count', 
                color=cat_var2,
                title=f"Association between {cat_var1} and {cat_var2}",
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True)
