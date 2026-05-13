"""
📁 Data - Load, preview, and manage your datasets
"""
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="DATA | FINESE2", page_icon="📁", layout="wide")

from utils.session_state import SessionManager
from utils.styling import  render_section_header
from utils.data_dictionary import render_data_dictionary
from utils.helpers import summarize_dataframe, get_column_types
from modules.data_manager import DataManager
from modules.ai_assistant import render_ai_settings_sidebar

SessionManager.init()


# Set current page in session state
st.session_state.current_page = "01_Data.py"

st.title("📁 DATA INGESTION")
st.caption("Load data from files, databases, or generate sample data")


# Tabs for different data sources
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload File", "🔗 Database", "🎲 Sample Data", "💾 Current Data"])

with tab1:
    render_section_header("Upload Your Data", "Drag and drop or browse for files")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls", "json", "parquet"],
        accept_multiple_files=False
    )

    if uploaded_file is not None:
        file_format = DataManager.detect_format(uploaded_file.name)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.info(f"Detected format: **{file_format.upper()}**")

            if file_format == "csv":
                encoding = st.selectbox("Encoding", ["utf-8", "latin1", "iso-8859-1", "cp1252"])
                sep = st.selectbox("Delimiter", [",", ";", "\t", "|"])
                decimal = st.selectbox("Decimal", [".", ","])
            elif file_format == "excel":
                st.info("Excel file detected. First sheet will be loaded.")

        with col2:
            # Add option for sampling large files
            sample_large_files = st.checkbox("Sample large files", value=True, 
                                            help="Automatically sample large datasets to improve performance")
            max_rows = st.number_input("Max rows when sampling", min_value=1000, max_value=100000, 
                                       value=10000, step=1000, 
                                       disabled=not sample_large_files)

            if st.button("🚀 Load Data", type="primary", use_container_width=True):
                with st.spinner("Loading data..."):
                    try:
                        if file_format == "csv":
                            df = DataManager.load_csv(uploaded_file.getvalue(), encoding=encoding, 
                                                     sep=sep, decimal=decimal, 
                                                     sample_if_large=sample_large_files, 
                                                     max_rows=max_rows)
                        elif file_format == "excel":
                            df, sheets = DataManager.load_excel(uploaded_file.getvalue(), 
                                                               sample_if_large=sample_large_files, 
                                                               max_rows=max_rows)
                            st.info(f"Available sheets: {', '.join(sheets)}")
                        elif file_format == "json":
                            df = DataManager.load_json(uploaded_file.getvalue(), 
                                                      sample_if_large=sample_large_files, 
                                                      max_rows=max_rows)
                        elif file_format == "parquet":
                            df = DataManager.load_parquet(uploaded_file.getvalue(), 
                                                         sample_if_large=sample_large_files, 
                                                         max_rows=max_rows)
                        else:
                            st.error("Unsupported file format")
                            df = None

                        if df is not None:
                            df = DataManager.auto_convert_types(df)
                            SessionManager.set_df(df, uploaded_file.name)
                            SessionManager.set("file_name", uploaded_file.name)
                            st.success(f"✅ Loaded {df.shape[0]:,} rows × {df.shape[1]} columns")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")

with tab2:
    render_section_header("Database Connection", "Connect to SQL databases")

    db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQLite", "SQL Server"])

    col1, col2 = st.columns(2)
    with col1:
        host = st.text_input("Host", "localhost")
        port = st.number_input("Port", value=5432 if db_type == "PostgreSQL" else 3306)
        database = st.text_input("Database Name")
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

    query = st.text_area("SQL Query", "SELECT * FROM your_table LIMIT 1000", height=100)

    # Add option for sampling large query results
    sample_large_results = st.checkbox("Sample large query results", value=True, 
                                      help="Automatically sample large query results to improve performance", key="db_sample")
    max_rows_db = st.number_input("Max rows when sampling", min_value=1000, max_value=100000, 
                                  value=10000, step=1000, 
                                  disabled=not sample_large_results, key="db_max_rows")

    if st.button("🔗 Connect & Load", type="primary"):
        with st.spinner("Connecting to database..."):
            try:
                if db_type == "PostgreSQL":
                    conn_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"
                elif db_type == "MySQL":
                    conn_str = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
                elif db_type == "SQLite":
                    conn_str = f"sqlite:///{database}"
                else:
                    conn_str = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}"

                df = DataManager.load_from_sql(conn_str, query, 
                                              sample_if_large=sample_large_results, 
                                              max_rows=max_rows_db)
                df = DataManager.auto_convert_types(df)
                SessionManager.set_df(df, f"{db_type}:{database}")
                SessionManager.set("file_name", f"{database}_query.csv")
                st.success(f"✅ Loaded {df.shape[0]:,} rows × {df.shape[1]} columns from database")
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

with tab3:
    render_section_header("Sample Datasets", "Use built-in sample data for exploration")

    sample_choice = st.selectbox(
        "Choose a sample dataset",
        ["Customer Analytics", "Sales Data", "Healthcare", "Financial", "E-commerce"]
    )

    if st.button("🎲 Generate Sample Data", type="primary"):
        with st.spinner("Generating sample data..."):
            df = DataManager.get_sample_data()
            SessionManager.set_df(df, f"sample_{sample_choice.lower().replace(' ', '_')}")
            SessionManager.set("file_name", f"sample_{sample_choice.lower().replace(' ', '_')}.csv")
            st.success(f"✅ Generated {df.shape[0]:,} rows of sample data")
            st.rerun()

with tab4:
    if SessionManager.has_data():
        df = SessionManager.get_df()
        summary = summarize_dataframe(df)

        st.subheader(f"Current Dataset: `{SessionManager.get('file_name')}`")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rows", f"{summary['rows']:,}")
        col2.metric("Columns", summary['columns'])
        col3.metric("Missing", f"{summary['missing_pct']:.1f}%")
        col4.metric("Duplicates", summary['duplicate_rows'])

        # Data Dictionary Section
        with st.expander("📚 Data Dictionary & Column Insights", expanded=False):
            render_data_dictionary(df)

        st.subheader("Data Preview")
        st.dataframe(df, use_container_width=True, height=400)

        st.subheader("Column Information")
        col_info = pd.DataFrame({
            'Column': df.columns,
            'Type': df.dtypes.astype(str),
            'Non-Null': df.notna().sum().values,
            'Null': df.isnull().sum().values,
            'Unique': df.nunique().values,
            'Sample': [str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else 'N/A' for col in df.columns]
        })
        st.dataframe(col_info, use_container_width=True, hide_index=True)

        # Export options
        st.subheader("Export Current Data")
        exports = DataManager.export_to_formats(df)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button("📄 CSV", exports["csv"], f"{SessionManager.get('file_name').split('.')[0]}.csv", use_container_width=True)
        with col2:
            st.download_button("📊 Excel", exports["excel"], f"{SessionManager.get('file_name').split('.')[0]}.xlsx", use_container_width=True)
        with col3:
            st.download_button("🗂️ JSON", exports["json"], f"{SessionManager.get('file_name').split('.')[0]}.json", use_container_width=True)
        with col4:
            st.download_button("🦆 Parquet", exports["parquet"], f"{SessionManager.get('file_name').split('.')[0]}.parquet", use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button("🪶 Feather", exports["feather"], f"{SessionManager.get('file_name').split('.')[0]}.feather", use_container_width=True)
        with col2:
            st.download_button("🌐 HTML", exports["html"], f"{SessionManager.get('file_name').split('.')[0]}.html", use_container_width=True)
        with col3:
            st.download_button("≜ LaTeX", exports["latex"], f"{SessionManager.get('file_name').split('.')[0]}.tex", use_container_width=True)
        with col4:
            if st.button("🗑️ Clear Data", type="secondary", use_container_width=True):
                SessionManager.reset_data()
                st.rerun()

    else:
        st.info("No data loaded. Use the tabs above to load data.")