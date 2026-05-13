"""
📈 Analysis - Statistical testing and regression
"""
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="ANALYSIS | FINESE2", page_icon="📈", layout="wide")

from utils.session_state import SessionManager
from utils.styling import  render_section_header
from modules.analyzer import StatisticalAnalyzer
from modules.ai_assistant import render_ai_settings_sidebar

SessionManager.init()

st.title("📈 Statistical Analysis")

if not SessionManager.has_data():
    st.warning("⚠️ No data loaded. Please load data in the Data section first.")
    st.stop()

df = SessionManager.get_df()

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()



# Option for sampling large datasets for analysis
sample_for_analysis = st.checkbox("Sample large datasets for analysis", value=True, 
                                help="Automatically sample large datasets to improve analysis performance", key="analysis_sample")
max_analysis_points = st.number_input("Max points for analysis", min_value=1000, max_value=50000, 
                                     value=10000, step=1000, 
                                     disabled=not sample_for_analysis, key="analysis_max_points")

# Descriptive Statistics
render_section_header("Descriptive Statistics", "")

desc_stats = StatisticalAnalyzer.descriptive_stats(df, sample_if_large=sample_for_analysis)
if not desc_stats.empty:
    st.dataframe(desc_stats, use_container_width=True)
else:
    st.info("No numeric columns for descriptive statistics")

# Statistical Tests
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Normality", "Correlation", "T-Test", "ANOVA", "Chi-Square"])

def display_normality_test():
    with tab1:
        with st.expander("🧪 Run Normality Test", expanded=True):
            render_section_header("Normality Test", "Test if data follows normal distribution")

            if numeric_cols:
                col = st.selectbox("Select column", numeric_cols, key="normality_col")
                method = st.selectbox("Test method", ["shapiro", "dagostino"], key="normality_method")

                if st.button("🧪 Run Normality Test", type="primary", key="normality_run"):
                    with st.spinner("Running normality test..."):
                        result = StatisticalAnalyzer.normality_test(df, col, method, sample_if_large=sample_for_analysis)

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Statistic", f"{result['statistic']:.4f}")
                        col2.metric("P-Value", f"{result['p_value']:.4f}")
                        col3.metric("Result", "Normal" if result['is_normal'] else "Not Normal")

                        st.info(result['interpretation'])
            else:
                st.info("No numeric columns available")

def display_correlation_analysis():
    with tab2:
        with st.expander("🔗 Run Correlation Analysis", expanded=True):
            render_section_header("Correlation Analysis", "")

            if len(numeric_cols) >= 2:
                method = st.selectbox("Correlation method", ["pearson", "spearman", "kendall"], key="corr_method")

                if st.button("🔗 Run Correlation Analysis", type="primary", key="corr_run"):
                    with st.spinner("Calculating correlations..."):
                        corr_matrix, corr_info = StatisticalAnalyzer.correlation_analysis(df, method, sample_if_large=sample_for_analysis)

                        st.subheader("Correlation Matrix")
                        st.dataframe(corr_matrix.style.background_gradient(cmap='RdYlGn', vmin=-1, vmax=1), 
                                    use_container_width=True)

                        if corr_info['significant_pairs']:
                            st.subheader("Significant Correlations")
                            st.dataframe(pd.DataFrame(corr_info['significant_pairs']), use_container_width=True, hide_index=True)
            else:
                st.info("Need at least 2 numeric columns")

def display_t_test():
    with tab3:
        with st.expander("🧪 Run T-Test", expanded=True):
            render_section_header("Independent T-Test", "Compare means between two groups")

            if numeric_cols and len(cat_cols) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    numeric_col = st.selectbox("Numeric variable", numeric_cols, key="ttest_num")
                with col2:
                    cat_col = st.selectbox("Grouping variable", cat_cols, key="ttest_cat")

                if st.button("🧪 Run T-Test", type="primary", key="ttest_run"):
                    with st.spinner("Running T-Test..."):
                        result = StatisticalAnalyzer.t_test(df, numeric_col, cat_col, sample_if_large=sample_for_analysis)

                        if 'error' in result:
                            st.error(result['error'])
                        else:
                            col1, col2, col3 = st.columns(3)
                            col1.metric("T-Statistic", f"{result['statistic']:.4f}")
                            col2.metric("P-Value", f"{result['p_value']:.4f}")
                            col3.metric("Significant", "Yes" if result['significant'] else "No")

                            st.markdown(f"**{result['interpretation']}**")
                            st.markdown(f"Group 1 Mean: {result['group1_mean']:.4f} | Group 2 Mean: {result['group2_mean']:.4f}")
            else:
                st.info("Need at least 1 numeric and 1 categorical column")

def display_anova():
    with tab4:
        with st.expander("🧪 Run ANOVA", expanded=True):
            render_section_header("One-Way ANOVA", "Compare means across multiple groups")

            if numeric_cols and len(cat_cols) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    numeric_col = st.selectbox("Numeric variable", numeric_cols, key="anova_num")
                with col2:
                    cat_col = st.selectbox("Grouping variable", cat_cols, key="anova_cat")

                if st.button("🧪 Run ANOVA", type="primary", key="anova_run"):
                    with st.spinner("Running ANOVA..."):
                        result = StatisticalAnalyzer.anova(df, numeric_col, cat_col, sample_if_large=sample_for_analysis)

                        col1, col2, col3 = st.columns(3)
                        col1.metric("F-Statistic", f"{result['statistic']:.4f}")
                        col2.metric("P-Value", f"{result['p_value']:.4f}")
                        col3.metric("Significant", "Yes" if result['significant'] else "No")

                        st.markdown(f"**{result['interpretation']}**")
                        st.markdown(f"Groups compared: {result['groups']}")
            else:
                st.info("Need at least 1 numeric and 1 categorical column")

def display_chi_square():
    with tab5:
        with st.expander("🧪 Run Chi-Square Test", expanded=True):
            render_section_header("Chi-Square Test", "Test independence between categorical variables")

            if len(cat_cols) >= 2:
                col1, col2 = st.columns(2)
                with col1:
                    col1_sel = st.selectbox("Variable 1", cat_cols, key="chi_col1")
                with col2:
                    col2_sel = st.selectbox("Variable 2", [c for c in cat_cols if c != col1_sel], key="chi_col2")

                if st.button("🧪 Run Chi-Square Test", type="primary", key="chi_run"):
                    with st.spinner("Running Chi-Square test..."):
                        result = StatisticalAnalyzer.chi_square_test(df, col1_sel, col2_sel, sample_if_large=sample_for_analysis)

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Chi2", f"{result['chi2']:.4f}")
                        col2.metric("P-Value", f"{result['p_value']:.4f}")
                        col3.metric("Significant", "Yes" if result['significant'] else "No")

                        st.markdown(f"**{result['interpretation']}**")
                        st.subheader("Contingency Table")
                        st.dataframe(result['contingency_table'], use_container_width=True)
            else:
                st.info("Need at least 2 categorical columns")

# Call the functions to display tab content
display_normality_test()
display_correlation_analysis()
display_t_test()
display_anova()
display_chi_square()

def display_regression():
    render_section_header("Multiple Linear Regression", "")

    if len(numeric_cols) >= 2:
        col1, col2 = st.columns([2, 3])
        with col1:
            target = st.selectbox("Target Variable", numeric_cols, key="reg_target")
        with col2:
            features = st.multiselect("Feature Variables", [c for c in numeric_cols if c != target], 
                                      default=[c for c in numeric_cols if c != target][:min(3, len(numeric_cols)-1)],
                                      key="reg_features")

        if st.button("📈 Run Regression", type="primary", key="reg_run") and features:
            with st.spinner("Fitting model..."):
                result = StatisticalAnalyzer.linear_regression(df, target, features, sample_if_large=sample_for_analysis)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("R²", f"{result['r_squared']:.4f}")
                col2.metric("Adj. R²", f"{result['adj_r_squared']:.4f}")
                col3.metric("F-Statistic", f"{result['f_statistic']:.2f}")
                col4.metric("AIC", f"{result['aic']:.2f}")

                # Coefficients
                coef_df = pd.DataFrame({
                    'Feature': list(result['coefficients'].keys()),
                    'Coefficient': list(result['coefficients'].values()),
                    'P-Value': [result['p_values'].get(k, 0) for k in result['coefficients'].keys()]
                })
                st.dataframe(coef_df, use_container_width=True, hide_index=True)
    else:
        st.info("Need at least 2 numeric columns for regression")