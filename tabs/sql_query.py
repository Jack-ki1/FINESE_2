import duckdb
import pandas as pd
import streamlit as st
import time
from datetime import datetime
from utils.data_utils import get_numeric_columns, get_categorical_columns, get_datetime_columns
from services.sql_service import execute_sql_query, get_table_schema
from utils.ui_utils import log_change
import logging

logger = logging.getLogger(__name__)
SECTION_HEADER_CLASS = "section-header"


def render_sql_tab(df) -> None:
    """
    SQL Query Interface - allows users to query their data using SQL
    """
    # Check if df is None or empty
    # If it's a DatasetContext, check its filtered_df property
    if df is None:
        st.warning("⚠️ No data loaded. Please upload data first.")
        return
    
    # Check if it's a DatasetContext object and get the DataFrame
    if hasattr(df, 'filtered_df'):
        df_to_use = df.filtered_df
    else:
        df_to_use = df
    
    if df_to_use.empty:
        st.warning("⚠️ No data loaded. Please upload data first.")
        return

    st.markdown(f'<div class="{SECTION_HEADER_CLASS}">🔍 Dynamic SQL Studio</div>', unsafe_allow_html=True)
    st.caption("Interactive SQL editor with data exploration tools — powered by DuckDB")

    # Register the DataFrame as a table
    conn = duckdb.connect()
    conn.register("data", df_to_use)

    # Sidebar with data exploration tools
    with st.sidebar:
        st.markdown("### 🛠️ SQL Toolkit")
        
        # Data preview
        with st.expander("📊 Data Preview", expanded=False):
            st.write(f"Shape: {df_to_use.shape[0]} × {df_to_use.shape[1]}")
            st.dataframe(df_to_use.head(3), use_container_width=True)
        
        # Schema explorer
        with st.expander("📋 Schema Explorer", expanded=True):
            try:
                schema = conn.execute("DESCRIBE data").fetchdf()
                st.dataframe(schema, use_container_width=True)
                
                # Column type summary
                col_types = df_to_use.dtypes.value_counts()
                st.write("**Column Types Summary:**")
                for dtype, count in col_types.items():
                    st.caption(f"{dtype}: {count} columns")
            except Exception as e:
                st.error(f"Schema error: {e}")
        
        # Quick stats
        with st.expander("📈 Quick Stats", expanded=False):
            st.write("**Numeric Columns:**")
            num_cols = get_numeric_columns(df_to_use)
            if num_cols:
                st.write(", ".join(num_cols[:5]))  # Show first 5
                if len(num_cols) > 5:
                    st.caption(f"... and {len(num_cols)-5} more")
            else:
                st.info("No numeric columns found")
                
            st.write("**Categorical Columns:**")
            cat_cols = get_categorical_columns(df_to_use)
            if cat_cols:
                st.write(", ".join(cat_cols[:5]))  # Show first 5
                if len(cat_cols) > 5:
                    st.caption(f"... and {len(cat_cols)-5} more")
            else:
                st.info("No categorical columns found")
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs([
        "✏️ Query Editor", 
        "💡 Query Builder", 
        "📊 Visualization", 
        "💾 History & Export"
    ])
    
    # Initialize session state for query history
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    with tab1:  # Query Editor
        # Layout for query editor
        editor_col1, editor_col2 = st.columns([4, 1])
        with editor_col1:
            query = st.text_area(
                "SQL Query", 
                value="SELECT *\nFROM data\nLIMIT 100", 
                height=300, 
                key="sql_query",
                placeholder="Enter your SQL query here...\n\nExample: SELECT column1, AVG(column2) FROM data GROUP BY column1"
            )
        with editor_col2:
            st.write("")  # Spacer
            run = st.button("▶ Execute Query", type="primary", use_container_width=True)
            if st.button("🧹 Clear", use_container_width=True):
                st.session_state.sql_query = "SELECT *\nFROM data\nLIMIT 100"
        
        # Execute query
        if run and query.strip():
            try:
                start_time = time.time()
                result = conn.execute(query).fetchdf()
                execution_time = time.time() - start_time
                
                # Add to history
                st.session_state.query_history.append({
                    'query': query.strip(),
                    'rows': len(result),
                    'time': execution_time,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                # Stats
                st.success(f"✅ Query executed in {execution_time:.2f}s. {len(result):,} rows returned.")
                
                stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                with stats_col1:
                    st.metric("Rows", f"{len(result):,}")
                with stats_col2:
                    st.metric("Cols", f"{len(result.columns)}")
                with stats_col3:
                    st.metric("Time", f"{execution_time:.2f}s")
                with stats_col4:
                    st.metric("Size", f"{result.memory_usage(deep=True).sum() / 1024:.1f} KB")
                
                # Results display
                st.subheader("Query Results")
                
                # Show different views based on data size
                if len(result) > 10000:
                    st.warning(f"Large result set ({len(result):,} rows) detected. Showing first 10,000 rows.")
                    result_display = result.head(10000)
                elif len(result) > 1000:
                    result_display = result
                else:
                    result_display = result
                
                # Interactive dataframe with copy/paste
                st.dataframe(result_display, use_container_width=True, height=400)
                
                log_change("Executed SQL query", f"Rows returned: {len(result)}, Execution time: {execution_time:.2f}s")
                
            except Exception as e:
                st.error(f"❌ Query failed: {e}")
                logger.error(f"SQL query error: {e}")
    
    with tab2:  # Query Builder
        st.markdown("### 🏗️ Visual Query Builder")
        
        # Query building components
        col1, col2 = st.columns(2)
        with col1:
            selected_cols = st.multiselect(
                "Select Columns", 
                options=["*"] + list(df_to_use.columns),
                default=["*"]
            )
        with col2:
            agg_options = {
                "None": "",
                "COUNT": "COUNT({})",
                "SUM": "SUM({})",
                "AVG": "AVG({})",
                "MIN": "MIN({})",
                "MAX": "MAX({})"
            }
            aggregation = st.selectbox("Aggregation", options=list(agg_options.keys()))
        
        # Where clause builder
        st.subheader("FilterWhere Conditions")
        where_col1, where_op1, where_val1 = st.columns(3)
        
        with where_col1:
            where_col = st.selectbox("Column", options=[""] + list(df_to_use.columns), key="where_col")
        with where_op1:
            operator = st.selectbox("Operator", ["=", "!=", ">", "<", ">=", "<=", "IN", "LIKE"], key="where_op")
        with where_val1:
            if where_col:
                # Provide appropriate input based on column type
                if df_to_use[where_col].dtype in ['int64', 'float64']:
                    where_val = st.number_input("Value", key="where_val")
                else:
                    where_val = st.text_input("Value", key="where_val")
            else:
                where_val = ""
        
        # Group by
        group_by_cols = st.multiselect("GROUP BY", options=[""] + list(df_to_use.columns), key="group_by")
        
        # Order by
        order_col, order_dir = st.columns(2)
        with order_col:
            order_by = st.selectbox("ORDER BY", options=[""] + list(df_to_use.columns), key="order_by")
        with order_dir:
            order_direction = st.selectbox("Direction", ["ASC", "DESC"], key="order_dir")
        
        # Limit
        limit = st.slider("LIMIT", 1, 10000, 100, key="limit")
        
        # Generate query button
        if st.button("⚡ Generate Query"):
            # Build query
            if selected_cols:
                if "*" in selected_cols:
                    select_clause = "*"
                else:
                    if aggregation != "None" and selected_cols:
                        select_clause = ", ".join([agg_options[aggregation].format(col) for col in selected_cols if col])
                    else:
                        select_clause = ", ".join(selected_cols)
            else:
                select_clause = "*"
            
            query_parts = [f"SELECT {select_clause}", "FROM data"]
            
            if where_col and where_val:
                if operator == "IN":
                    query_parts.append(f"WHERE {where_col} IN ({where_val})")
                elif operator == "LIKE":
                    query_parts.append(f"WHERE {where_col} LIKE '%{where_val}%'")
                else:
                    query_parts.append(f"WHERE {where_col} {operator} {repr(where_val) if isinstance(where_val, str) else where_val}")
            
            if group_by_cols and any(group_by_cols):
                query_parts.append(f"GROUP BY {', '.join([col for col in group_by_cols if col])}")
            
            if order_by:
                query_parts.append(f"ORDER BY {order_by} {order_direction}")
            
            query_parts.append(f"LIMIT {limit}")
            
            generated_query = " ".join(query_parts)
            
            # Set the generated query in the main editor
            st.session_state.sql_query = generated_query
            st.code(generated_query, language="sql")
    
    with tab3:  # Visualization
        st.markdown("### 📊 Data Visualization")
        
        if 'result' in locals() and not locals()['result'].empty:
            viz_data = locals()['result']
        elif 'result_display' in locals() and not locals()['result_display'].empty:
            viz_data = locals()['result_display']
        else:
            st.info("Run a query in the Query Editor tab to visualize results")
            st.stop()
        
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            x_axis = st.selectbox("X-Axis", options=viz_data.columns)
        with viz_col2:
            y_axis = st.selectbox("Y-Axis", options=["None"] + list(viz_data.columns))
        
        chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Scatter", "Histogram"])
        
        if x_axis:
            import plotly.express as px
            
            if chart_type == "Line":
                if y_axis and y_axis != "None":
                    fig = px.line(viz_data, x=x_axis, y=y_axis, title=f"Line Chart: {x_axis} vs {y_axis}")
                else:
                    fig = px.line(viz_data, x=x_axis, title=f"Line Chart: {x_axis}")
            elif chart_type == "Bar":
                if y_axis and y_axis != "None":
                    fig = px.bar(viz_data, x=x_axis, y=y_axis, title=f"Bar Chart: {x_axis} vs {y_axis}")
                else:
                    # Count occurrences of x-axis values
                    counts = viz_data[x_axis].value_counts().reset_index()
                    counts.columns = [x_axis, 'count']
                    fig = px.bar(counts, x=x_axis, y='count', title=f"Bar Chart: {x_axis} Counts")
            elif chart_type == "Scatter":
                if y_axis and y_axis != "None":
                    fig = px.scatter(viz_data, x=x_axis, y=y_axis, title=f"Scatter Plot: {x_axis} vs {y_axis}")
                else:
                    st.warning("Scatter plots require both X and Y axes")
            elif chart_type == "Histogram":
                fig = px.histogram(viz_data, x=x_axis, title=f"Histogram: {x_axis}")
            
            if 'fig' in locals():
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:  # History & Export
        st.markdown("### 📜 Query History")
        
        if st.session_state.query_history:
            # Show recent queries
            for i, record in enumerate(reversed(st.session_state.query_history[-10:])):  # Last 10 queries
                with st.expander(f"Query at {record['timestamp']} ({record['rows']} rows, {record['time']:.2f}s)", expanded=False):
                    st.code(record['query'], language='sql')
                    if st.button(f"Reuse Query #{len(st.session_state.query_history)-i}", key=f"reuse_{i}"):
                        st.session_state.sql_query = record['query']
                        st.success("Query copied to editor!")
        else:
            st.info("No queries executed yet")
        
        st.markdown("### 💾 Export Options")
        
        # Export query results if available
        if 'result' in locals() and not locals()['result'].empty:
            result_export = locals()['result']
            
            export_col1, export_col2, export_col3 = st.columns(3)
            
            with export_col1:
                csv = result_export.to_csv(index=False)
                st.download_button(
                    label="📥 CSV Export",
                    data=csv,
                    file_name=f"sql_query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with export_col2:
                json_str = result_export.to_json(orient='records', date_format='iso', indent=2)
                st.download_button(
                    label="📥 JSON Export",
                    data=json_str,
                    file_name=f"sql_query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with export_col3:
                try:
                    from io import BytesIO
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        result_export.to_excel(writer, index=False, sheet_name='QueryResult')
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Excel Export",
                        data=buffer.getvalue(),
                        file_name=f"sql_query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                except ImportError:
                    st.info("Install `xlsxwriter` for Excel export")
        
        else:
            st.info("Run a query to enable export options")
    
    conn.close()