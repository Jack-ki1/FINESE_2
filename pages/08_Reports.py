"""
📝 Reports - Generate and export professional reports
"""
import streamlit as st
import pandas as pd
import base64

st.set_page_config(page_title="REPORTS | FINESE2", page_icon="📝", layout="wide")

from utils.session_state import SessionManager
from utils.styling import render_section_header
from modules.report_generator import ReportGenerator
from modules.data_manager import DataManager
from modules.ai_assistant import render_ai_settings_sidebar

SessionManager.init()


st.title("📝 Report Generator")

if not SessionManager.has_data():
    st.warning("⚠️ No data loaded. Please load data in the Data section first.")
    st.stop()

df = SessionManager.get_df()


render_section_header("Generate Reports", "Export your analysis in multiple formats")

# Report configuration
col1, col2 = st.columns([1, 2])
with col1:
    report_title = st.text_input("Report Title", f"Data Report - {SessionManager.get('file_name', 'Dataset')}")
    include_sections = st.multiselect(
        "Include Sections",
        ["Overview", "Column Summary", "Numeric Statistics", "Categorical Summary", "Missing Values", "Correlations"],
        default=["Overview", "Column Summary", "Numeric Statistics"]
    )

with col2:
    st.info("""
    **Report Types:**
    - **HTML**: Styled web report with standard formatting, interactive tables
    - **Excel**: Multi-sheet workbook with formatted headers
    - **Markdown**: Plain text report for documentation
    """)

# Generate buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Generate HTML Report", type="primary", use_container_width=True):
        with st.spinner("Generating HTML report..."):
            sections = {}
            if "Correlations" in include_sections and len(df.select_dtypes(include=['number']).columns) >= 2:
                corr = df.select_dtypes(include=['number']).corr()
                sections["Correlations"] = corr.to_string()

            html = ReportGenerator.generate_html_report(df, report_title, sections)

            st.download_button(
                "⬇️ Download HTML Report",
                html.encode(),
                f"{report_title.replace(' ', '_')}.html",
                "text/html",
                use_container_width=True
            )

            # Preview
            with st.expander("Preview HTML Report"):
                st.components.v1.html(html, height=600, scrolling=True)

with col2:
    if st.button("📊 Generate Excel Report", type="primary", use_container_width=True):
        with st.spinner("Generating Excel workbook..."):
            sheets = {"Data": df}

            if "Numeric Statistics" in include_sections:
                numeric_df = df.select_dtypes(include=['number'])
                if not numeric_df.empty:
                    sheets["Numeric Stats"] = numeric_df.describe().T

            if "Categorical Summary" in include_sections:
                cat_df = df.select_dtypes(include=['object', 'category'])
                if not cat_df.empty:
                    cat_summary = pd.DataFrame({
                        'Column': cat_df.columns,
                        'Unique': [cat_df[c].nunique() for c in cat_df.columns],
                        'Top Value': [cat_df[c].mode().iloc[0] if not cat_df[c].mode().empty else 'N/A' for c in cat_df.columns]
                    })
                    sheets["Categorical Stats"] = cat_summary

            if "Missing Values" in include_sections:
                missing_df = pd.DataFrame({
                    'Column': df.columns,
                    'Missing Count': df.isnull().sum().values,
                    'Missing %': (df.isnull().mean().values * 100).round(2)
                })
                sheets["Missing Values"] = missing_df

            excel_bytes = ReportGenerator.generate_excel_report(df, sheets)

            st.download_button(
                "⬇️ Download Excel Report",
                excel_bytes,
                f"{report_title.replace(' ', '_')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

with col3:
    if st.button("📝 Generate Markdown Report", type="primary", use_container_width=True):
        with st.spinner("Generating Markdown report..."):
            md = ReportGenerator.generate_markdown_report(df, report_title)

            st.download_button(
                "⬇️ Download Markdown Report",
                md.encode(),
                f"{report_title.replace(' ', '_')}.md",
                "text/markdown",
                use_container_width=True
            )

            with st.expander("Preview Markdown"):
                st.markdown(md)

# Quick exports
render_section_header("Quick Exports", "Export raw data in various formats")

exports = DataManager.export_to_formats(df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.download_button("📄 CSV", exports["csv"], 
                      f"{SessionManager.get('file_name', 'data').split('.')[0]}.csv", 
                      use_container_width=True)
with col2:
    st.download_button("📊 Excel", exports["excel"],
                      f"{SessionManager.get('file_name', 'data').split('.')[0]}.xlsx",
                      use_container_width=True)
with col3:
    st.download_button("🗂️ JSON", exports["json"],
                      f"{SessionManager.get('file_name', 'data').split('.')[0]}.json",
                      use_container_width=True)
with col4:
    st.download_button("🦆 Parquet", exports["parquet"],
                      f"{SessionManager.get('file_name', 'data').split('.')[0]}.parquet",
                      use_container_width=True)