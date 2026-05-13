"""
📊 Visualization - Interactive chart builder and dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="VISUALIZATION | FINESE2", page_icon="📊", layout="wide")

from utils.session_state import SessionManager
from utils.styling import render_section_header
from modules.visualizer import Visualizer
from modules.ai_assistant import render_ai_settings_sidebar

SessionManager.init()
#apply_custom_css()

st.title("📊 Visualization Studio")

if not SessionManager.has_data():
    st.warning("⚠️ No data loaded. Please load data in the Data section first.")
    st.stop()

df = SessionManager.get_df()

# Helper function to render charts based on widget type
def render_widget_chart(widget, df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if widget['type'] == 'bar_chart':
        # Ensure x and y have compatible lengths
        x_data = widget['x']
        y_data = widget['y']
        
        # If x_data is a list but y_data is a column name, get the column data
        if isinstance(x_data, list) and isinstance(y_data, str) and y_data in df.columns:
            y_data = df[y_data].iloc[:len(x_data)].tolist()
        elif isinstance(y_data, list) and isinstance(x_data, str) and x_data in df.columns:
            x_data = df[x_data].iloc[:len(y_data)].tolist()
        elif isinstance(x_data, str) and isinstance(y_data, str):
            # Both are column names, use the shorter one
            min_len = min(len(df[x_data]), len(df[y_data]))
            x_data = df[x_data].iloc[:min_len].tolist()
            y_data = df[y_data].iloc[:min_len].tolist()
        
        # Create a temporary dataframe with compatible lengths
        temp_df = pd.DataFrame({'x': x_data, 'y': y_data})
        return Visualizer.bar_chart(temp_df, x='x', y='y', title=widget['title'])
    elif widget['type'] == 'line_chart':
        if isinstance(widget['x'], list) and isinstance(widget['y'], list):
            df_temp = pd.DataFrame({'x': widget['x'], 'y': widget['y']})
            return Visualizer.line_chart(df_temp, x='x', y='y', title=widget['title'])
        else:
            x_col, y_col = widget['x'], widget['y']
            # Ensure both columns have same length
            min_len = min(len(df[x_col]), len(df[y_col]))
            temp_df = pd.DataFrame({
                'x': df[x_col].iloc[:min_len].tolist(),
                'y': df[y_col].iloc[:min_len].tolist()
            })
            return Visualizer.line_chart(temp_df, x='x', y='y', title=widget['title'])
    elif widget['type'] == 'pie_chart':
        # Handle both cases: when we only have the category column and when we have both category and values columns
        if 'values_col' in widget:
            # If values_col is provided, use it for values
            pie_data = df.groupby(widget['col'])[widget['values_col']].sum().reset_index()
            return Visualizer.pie_chart(
                pie_data, 
                names=widget['col'], 
                values=widget['values_col'],
                title=widget['title']
            )
        else:
            # Otherwise, just count occurrences of each category
            pie_data = df[widget['col']].value_counts().head(10).reset_index()
            pie_data.columns = [widget['col'], 'count']
            return Visualizer.pie_chart(
                pie_data, 
                names=widget['col'], 
                values='count',
                title=widget['title']
            )
    elif widget['type'] == 'heatmap':
        return Visualizer.correlation_heatmap(
            df.select_dtypes(include=[np.number]), 
            method=widget['method'],
            title=widget['title']
        )
    elif widget['type'] == 'area_chart':
        if isinstance(widget['x'], list) and isinstance(widget['y'], list):
            df_temp = pd.DataFrame({'x': widget['x'], 'y': widget['y']})
            return Visualizer.area_chart(df_temp, x='x', y='y', title=widget['title'])
        else:
            x_col, y_col = widget['x'], widget['y']
            # Ensure both columns have same length
            min_len = min(len(df[x_col]), len(df[y_col]))
            temp_df = pd.DataFrame({
                'x': df[x_col].iloc[:min_len].tolist(),
                'y': df[y_col].iloc[:min_len].tolist()
            })
            return Visualizer.area_chart(temp_df, x='x', y='y', title=widget['title'])
    elif widget['type'] == 'box_plot':
        y_col = widget['y']
        x_col = widget['x']
        if x_col and x_col in df.columns:
            return Visualizer.box_plot(df, y=y_col, x=x_col, title=widget['title'])
        else:
            return Visualizer.box_plot(df, y=y_col, title=widget['title'])
    elif widget['type'] == 'scatter_plot':
        x_col, y_col = widget['x'], widget['y']
        # Ensure both columns have same length
        min_len = min(len(df[x_col]), len(df[y_col]))
        temp_df = pd.DataFrame({
            'x': df[x_col].iloc[:min_len].tolist(),
            'y': df[y_col].iloc[:min_len].tolist()
        })
        return Visualizer.scatter_plot(temp_df, x='x', y='y', title=widget['title'])
    elif widget['type'] == 'treemap':
        return Visualizer.treemap(
            df, 
            path=widget['path'], 
            values=widget['values'],
            title=widget['title']
        )
    elif widget['type'] == 'funnel_chart':
        if isinstance(widget['x'], list) and isinstance(widget['y'], list):
            df_funnel = pd.DataFrame({'x': widget['x'], 'y': widget['y']})
            return Visualizer.funnel_chart(df_funnel, x='x', y='y', title=widget['title'])
        else:
            x_col, y_col = widget['x'], widget['y']
            # Ensure both columns have same length
            min_len = min(len(df[x_col]), len(df[y_col]))
            temp_df = pd.DataFrame({
                'x': df[x_col].iloc[:min_len].tolist(),
                'y': df[y_col].iloc[:min_len].tolist()
            })
            return Visualizer.funnel_chart(temp_df, x='x', y='y', title=widget['title'])
    elif widget['type'] == 'gauge_chart':
        return Visualizer.gauge_chart(
            widget['value'], 
            min_val=widget.get('min_val', 0), 
            max_val=widget.get('max_val', 100),
            title=widget['title']
        )
    elif widget['type'] == 'correlation_heatmap':
        return Visualizer.correlation_heatmap(
            df.select_dtypes(include=[np.number]), 
            method=widget['method'],
            title=widget['title']
        )
    elif widget['type'] == 'histogram':
        return Visualizer.histogram(
            df, 
            x=widget['col'],
            title=widget['title']
        )
    elif widget['type'] == 'waterfall_chart':
        return Visualizer.waterfall_chart(
            widget['categories'],
            widget['values'],
            title=widget['title']
        )
    elif widget['type'] == 'violin_plot':
        y_col = widget['y']
        x_col = widget['x']
        if x_col and x_col in df.columns:
            return Visualizer.violin_plot(df, y=y_col, x=x_col, title=widget['title'])
        else:
            return Visualizer.violin_plot(df, y=y_col, title=widget['title'])
    elif widget['type'] == 'radar_chart':
        return Visualizer.radar_chart(
            df, 
            vars=widget['vars'] if 'vars' in widget else numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols,
            title=widget['title']
        )
    elif widget['type'] == 'sunburst':
        return Visualizer.sunburst(
            df, 
            path=widget['path'] if 'path' in widget else cat_cols[:3] if len(cat_cols) >= 3 else cat_cols,
            values=widget['values'] if 'values' in widget else numeric_cols[0] if numeric_cols else 'count',
            title=widget['title']
        )
    elif widget['type'] == 'parallel_coordinates':
        selected_cols = widget['columns'] if 'columns' in widget else numeric_cols[:min(5, len(numeric_cols))]
        return Visualizer.parallel_coordinates(
            df, 
            columns=selected_cols,
            title=widget['title']
        )
    elif widget['type'] == 'sankey_diagram':
        # For Sankey, we need categorical columns for source/target and a numeric for values
        if 'source' in widget and 'target' in widget and 'value' in widget:
            return Visualizer.sankey_diagram(
                df, 
                source=widget['source'], 
                target=widget['target'], 
                value=widget['value'],
                title=widget['title']
            )
    return None

# Dashboard Builder Tab
dashboard_tab, chart_builder_tab = st.tabs(["📈 Dashboard Builder", "🎨 Chart Builder"])

with dashboard_tab:
    render_section_header("Dashboard Builder", "Create custom dashboards with drag-and-drop widgets")
    
    # Dashboard templates
    col1, col2, col3 = st.columns(3)
    with col1:
        template = st.selectbox("Dashboard Template", 
                               ["Blank Canvas", "Marketing Analytics", "Finance Dashboard", "Operations Metrics"])
    with col2:
        dashboard_title = st.text_input("Dashboard Title", "My Custom Dashboard")
    with col3:
        auto_save = st.toggle("Auto-save Dashboard", value=True)
    
    # Dashboard layout options
    layout_options = st.radio("Layout Style", ["Grid", "Freeform (coming soon)"], horizontal=True)
    
    # Store dashboard info in session state
    if 'active_dashboard' not in st.session_state:
        st.session_state['active_dashboard'] = None

    if st.button("🚀 Create New Dashboard", type="primary", use_container_width=True):
        # Get numeric and categorical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Create a new dashboard with default widgets based on the template
        dashboard_widgets = []
        
        # Define widgets based on template
        if template == "Marketing Analytics":
            # Marketing-specific KPIs and charts
            dashboard_widgets.extend([
                {"id": "kpi1", "type": "kpi", "title": "Total Revenue", "value": df[numeric_cols[0]].sum() if numeric_cols else 0, "prev_value": df[numeric_cols[0]].sum()*0.9 if numeric_cols else 0},
                {"id": "kpi2", "type": "kpi", "title": "Conversion Rate", "value": df[numeric_cols[1]].mean() if len(numeric_cols) > 1 else 0, "prev_value": df[numeric_cols[1]].mean()*0.8 if len(numeric_cols) > 1 else 0},
                {"id": "kpi3", "type": "kpi", "title": "Customer Acquisition", "value": df.shape[0], "prev_value": df.shape[0]*0.9},
                {"id": "kpi4", "type": "kpi", "title": "ROI", "value": ((df[numeric_cols[0]].sum() if numeric_cols else 0) / max((df[numeric_cols[1]].sum() if len(numeric_cols) > 1 else 1), 1)) * 100, "prev_value": 0},
                {"id": "kpi5", "type": "kpi", "title": "Avg. Order Value", "value": (df[numeric_cols[0]].sum() if numeric_cols else 0) / max(df.shape[0], 1), "prev_value": 0},
                {"id": "kpi6", "type": "kpi", "title": "Cost Per Lead", "value": (df[numeric_cols[1]].sum() if len(numeric_cols) > 1 else 0) / max(df.shape[0], 1), "prev_value": 0},
                # First 6 charts
                {"id": "chart1", "type": "bar_chart", "title": "Revenue by Category", "x": cat_cols[0] if cat_cols else df.index[:min(len(df), 10)].tolist(), "y": numeric_cols[0] if numeric_cols else df.index[:min(len(df), 10)]},
                {"id": "chart2", "type": "line_chart", "title": "Conversion Trend", "x": df.index[:min(len(df), 20)], "y": numeric_cols[1][:min(len(df), 20)] if len(numeric_cols) > 1 else df.index[:min(len(df), 20)]},
                {"id": "chart3", "type": "pie_chart", "title": "Traffic Sources", "col": cat_cols[0] if cat_cols else df.index.name or "index"},
                {"id": "chart4", "type": "heatmap", "title": "Correlation Heatmap", "method": "pearson"},
                {"id": "chart5", "type": "area_chart", "title": "Engagement Over Time", "x": df.index[:min(len(df), 20)], "y": numeric_cols[2][:min(len(df), 20)] if len(numeric_cols) > 2 else df.index[:min(len(df), 20)]},
                {"id": "chart6", "type": "scatter_plot", "title": "Clicks vs Conversions", "x": numeric_cols[3] if len(numeric_cols) > 3 else df.index.name or "index", "y": numeric_cols[1] if len(numeric_cols) > 1 else df.index.name or "index"},
                # Additional 6 charts
                {"id": "chart7", "type": "treemap", "title": "Revenue by Segment", "path": [cat_cols[0]] if cat_cols else ["Segment"], "values": numeric_cols[0] if numeric_cols else df.index.name or "value"},
                {"id": "chart8", "type": "funnel_chart", "title": "Marketing Funnel", "x": cat_cols[0] if cat_cols else ["Awareness", "Interest", "Consideration", "Purchase"], "y": numeric_cols[0] if numeric_cols else [1000, 750, 500, 250]},
                {"id": "chart9", "type": "box_plot", "title": "Revenue Distribution", "y": numeric_cols[0] if numeric_cols else df.index.name or "value", "x": cat_cols[0] if cat_cols else None},
                {"id": "chart10", "type": "violin_plot", "title": "Revenue Spread", "y": numeric_cols[0] if numeric_cols else df.index.name or "value", "x": cat_cols[0] if cat_cols else None},
                {"id": "chart11", "type": "radar_chart", "title": "Channel Performance", "vars": numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols},
                {"id": "chart12", "type": "sunburst", "title": "Revenue Breakdown", "path": cat_cols[:3] if len(cat_cols) >= 3 else cat_cols if cat_cols else ["Level1", "Level2"], "values": numeric_cols[0] if numeric_cols else "count"},
                # Even more visuals
                {"id": "chart13", "type": "histogram", "title": "Visitor Count Distribution", "col": numeric_cols[0] if numeric_cols else df.index.name or "index"},
                {"id": "chart14", "type": "waterfall_chart", "title": "Revenue Changes", "categories": ["Jan", "Feb", "Mar", "Apr", "May"], "values": [100, 20, -10, 30, 15]},
                {"id": "chart15", "type": "gauge_chart", "title": "Performance Index", "value": 78, "min_val": 0, "max_val": 100},
                {"id": "chart16", "type": "parallel_coordinates", "title": "Multi-Dimensional Analysis", "columns": numeric_cols[:min(5, len(numeric_cols))] if numeric_cols else ["Dim1"]},
                {"id": "chart17", "type": "sankey_diagram", "title": "Customer Journey Flow", "source": cat_cols[0] if cat_cols else "source", "target": cat_cols[1] if len(cat_cols) > 1 else "target", "value": numeric_cols[0] if numeric_cols else "value"},
                {"id": "chart18", "type": "sunburst", "title": "Campaign Performance", "path": cat_cols[:3] if len(cat_cols) >= 3 else cat_cols if cat_cols else ["Level1", "Level2"], "values": numeric_cols[1] if len(numeric_cols) > 1 else "count"}
            ])
        elif template == "Finance Dashboard":
            # Finance-specific KPIs and charts
            dashboard_widgets.extend([
                {"id": "kpi1", "type": "kpi", "title": "Total Assets", "value": df[numeric_cols[0]].sum() if numeric_cols else 0, "prev_value": df[numeric_cols[0]].sum()*0.95 if numeric_cols else 0},
                {"id": "kpi2", "type": "kpi", "title": "Net Profit Margin", "value": ((df[numeric_cols[0]].sum() if numeric_cols else 0) / max((df[numeric_cols[1]].sum() if len(numeric_cols) > 1 else 1), 1)) * 100, "prev_value": 0},
                {"id": "kpi3", "type": "kpi", "title": "Cash Flow", "value": (df[numeric_cols[0]].sum() if numeric_cols else 0) - (df[numeric_cols[1]].sum() if len(numeric_cols) > 1 else 0), "prev_value": 0},
                {"id": "kpi4", "type": "kpi", "title": "Debt-to-Equity", "value": ((df[numeric_cols[2]].sum() if len(numeric_cols) > 2 else 0) / max((df[numeric_cols[3]].sum() if len(numeric_cols) > 3 else 1), 1)) if numeric_cols else 0, "prev_value": 0},
                {"id": "kpi5", "type": "kpi", "title": "ROE", "value": ((df[numeric_cols[0]].sum() if numeric_cols else 0) / max((df[numeric_cols[3]].sum() if len(numeric_cols) > 3 else 1), 1)) * 100, "prev_value": 0},
                {"id": "kpi6", "type": "kpi", "title": "Current Ratio", "value": ((df[numeric_cols[4]].sum() if len(numeric_cols) > 4 else 0) / max((df[numeric_cols[5]].sum() if len(numeric_cols) > 5 else 1), 1)) if len(numeric_cols) > 5 else 0, "prev_value": 0},
                # First 6 charts
                {"id": "chart1", "type": "area_chart", "title": "Revenue Growth", "x": df.index[:min(len(df), 20)], "y": numeric_cols[0][:min(len(df), 20)] if numeric_cols else df.index[:min(len(df), 20)]},
                {"id": "chart2", "type": "box_plot", "title": "Profit Distribution", "y": numeric_cols[0] if numeric_cols else df.index.name or "index", "x": cat_cols[0] if cat_cols else None},
                {"id": "chart3", "type": "scatter_plot", "title": "Risk vs Return", "x": numeric_cols[0] if numeric_cols else df.index.name or "index", "y": numeric_cols[1] if len(numeric_cols) > 1 else df.index.name or "index"},
                {"id": "chart4", "type": "gauge_chart", "title": "Performance Index", "value": 75, "min_val": 0, "max_val": 100},
                {"id": "chart5", "type": "correlation_heatmap", "title": "Financial Correlations", "method": "pearson"},
                {"id": "chart6", "type": "histogram", "title": "Return Distribution", "col": numeric_cols[0] if numeric_cols else df.index.name or "index"},
                # Additional 6 charts
                {"id": "chart7", "type": "treemap", "title": "Asset Allocation", "path": [cat_cols[0]] if cat_cols else ["Asset Type"], "values": numeric_cols[0] if numeric_cols else df.index.name or "value"},
                {"id": "chart8", "type": "waterfall_chart", "title": "Financial Performance", "categories": ["Revenue", "Expenses", "Tax", "Net Income"], "values": [df[numeric_cols[0]].sum() if numeric_cols else 1000, -(df[numeric_cols[1]].sum() if len(numeric_cols) > 1 else 300), -(df[numeric_cols[2]].sum() if len(numeric_cols) > 2 else 100), df[numeric_cols[0]].sum() - (df[numeric_cols[1]].sum() if len(numeric_cols) > 1 else 300) - (df[numeric_cols[2]].sum() if len(numeric_cols) > 2 else 100) if numeric_cols else 600]},
                {"id": "chart9", "type": "radar_chart", "title": "Financial Ratios", "vars": numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols},
                {"id": "chart10", "type": "funnel_chart", "title": "Budget Flow", "x": cat_cols[0] if cat_cols else ["Revenue", "Operating Expenses", "Taxes", "Net Income"], "y": numeric_cols[0] if numeric_cols else [1000, 600, 200, 200]},
                {"id": "chart11", "type": "parallel_coordinates", "title": "Multi-Factor Analysis", "columns": numeric_cols[:min(5, len(numeric_cols))] if numeric_cols else ["Factor1"]},
                {"id": "chart12", "type": "sunburst", "title": "Expense Breakdown", "path": cat_cols[:3] if len(cat_cols) >= 3 else cat_cols if cat_cols else ["Level1", "Level2"], "values": numeric_cols[0] if numeric_cols else "count"},
                # Even more visuals
                {"id": "chart13", "type": "bar_chart", "title": "Quarterly Results", "x": df.index[:min(len(df), 4)], "y": numeric_cols[1][:min(len(df), 4)] if len(numeric_cols) > 1 else df.index[:min(len(df), 4)]},
                {"id": "chart14", "type": "line_chart", "title": "Cash Flow Trend", "x": df.index[:min(len(df), 12)], "y": numeric_cols[2][:min(len(df), 12)] if len(numeric_cols) > 2 else df.index[:min(len(df), 12)]},
                {"id": "chart15", "type": "violin_plot", "title": "Volatility Analysis", "y": numeric_cols[3] if len(numeric_cols) > 3 else df.index.name or "value", "x": cat_cols[0] if cat_cols else None},
                {"id": "chart16", "type": "area_chart", "title": "Cumulative Returns", "x": df.index[:min(len(df), 20)], "y": numeric_cols[4][:min(len(df), 20)] if len(numeric_cols) > 4 else df.index[:min(len(df), 20)]},
                {"id": "chart17", "type": "pie_chart", "title": "Asset Distribution", "col": cat_cols[0] if cat_cols else df.index.name or "index", "values_col": numeric_cols[0] if numeric_cols else "count"},
                {"id": "chart18", "type": "box_plot", "title": "Risk Distribution", "y": numeric_cols[5] if len(numeric_cols) > 5 else df.index.name or "value", "x": cat_cols[1] if len(cat_cols) > 1 else None}
            ])
        elif template == "Operations Metrics":
            # Operations-specific KPIs and charts
            dashboard_widgets.extend([
                {"id": "kpi1", "type": "kpi", "title": "Efficiency Score", "value": 85.5, "prev_value": 82.3},
                {"id": "kpi2", "type": "kpi", "title": "Cycle Time", "value": 12.3, "prev_value": 14.2},
                {"id": "kpi3", "type": "kpi", "title": "Quality Rate", "value": 97.2, "prev_value": 96.8},
                {"id": "kpi4", "type": "kpi", "title": "Capacity Utilization", "value": 88.7, "prev_value": 85.1},
                {"id": "kpi5", "type": "kpi", "title": "On-Time Delivery", "value": 95.3, "prev_value": 94.1},
                {"id": "kpi6", "type": "kpi", "title": "Cost Variance", "value": 2.1, "prev_value": 2.8},
                # First 6 charts
                {"id": "chart1", "type": "line_chart", "title": "Production Trend", "x": df.index[:min(len(df), 20)], "y": numeric_cols[0][:min(len(df), 20)] if numeric_cols else df.index[:min(len(df), 20)]},
                {"id": "chart2", "type": "bar_chart", "title": "Defects by Category", "x": cat_cols[0] if cat_cols else "Index", "y": numeric_cols[0] if numeric_cols else df.index.name or "index"},
                {"id": "chart3", "type": "treemap", "title": "Resource Allocation", "path": [cat_cols[0]] if cat_cols else ["Index"], "values": numeric_cols[0] if numeric_cols else df.index.name or "index"},
                {"id": "chart4", "type": "funnel_chart", "title": "Process Conversion", "x": cat_cols[0] if cat_cols else ["Stage 1", "Stage 2", "Stage 3"], "y": numeric_cols[0] if numeric_cols else [100, 75, 50]},
                {"id": "chart5", "type": "box_plot", "title": "Process Times", "y": numeric_cols[1] if len(numeric_cols) > 1 else df.index.name or "index", "x": cat_cols[0] if cat_cols else None},
                {"id": "chart6", "type": "waterfall_chart", "title": "Performance Change", "categories": ["Baseline", "Factor 1", "Factor 2", "Factor 3", "Current"], "values": [100, 15, -10, 20, 125]},
                # Additional 6 charts
                {"id": "chart7", "type": "violin_plot", "title": "Process Variation", "y": numeric_cols[0] if numeric_cols else df.index.name or "value", "x": cat_cols[0] if cat_cols else None},
                {"id": "chart8", "type": "radar_chart", "title": "Operational Excellence", "vars": numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols},
                {"id": "chart9", "type": "scatter_plot", "title": "Efficiency vs Cost", "x": numeric_cols[0] if numeric_cols else df.index.name or "index", "y": numeric_cols[1] if len(numeric_cols) > 1 else df.index.name or "index"},
                {"id": "chart10", "type": "area_chart", "title": "Capacity Utilization Trend", "x": df.index[:min(len(df), 20)], "y": numeric_cols[2][:min(len(df), 20)] if len(numeric_cols) > 2 else df.index[:min(len(df), 20)]},
                {"id": "chart11", "type": "parallel_coordinates", "title": "Process Parameters", "columns": numeric_cols[:min(5, len(numeric_cols))] if numeric_cols else ["Parameter1"]},
                {"id": "chart12", "type": "sunburst", "title": "Quality Breakdown", "path": cat_cols[:3] if len(cat_cols) >= 3 else cat_cols if cat_cols else ["Level1", "Level2"], "values": numeric_cols[0] if numeric_cols else "count"},
                # Even more visuals
                {"id": "chart13", "type": "correlation_heatmap", "title": "Process Correlations", "method": "spearman"},
                {"id": "chart14", "type": "histogram", "title": "Output Distribution", "col": numeric_cols[1] if len(numeric_cols) > 1 else df.index.name or "index"},
                {"id": "chart15", "type": "gauge_chart", "title": "Quality Index", "value": 92, "min_val": 0, "max_val": 100},
                {"id": "chart16", "type": "bar_chart", "title": "Team Performance", "x": cat_cols[0] if cat_cols else df.index[:min(len(df), 5)], "y": numeric_cols[3] if len(numeric_cols) > 3 else df.index[:min(len(df), 5)]},
                {"id": "chart17", "type": "line_chart", "title": "Defect Trend", "x": df.index[:min(len(df), 20)], "y": numeric_cols[4][:min(len(df), 20)] if len(numeric_cols) > 4 else df.index[:min(len(df), 20)]},
                {"id": "chart18", "type": "pie_chart", "title": "Resource Distribution", "col": cat_cols[1] if len(cat_cols) > 1 else df.index.name or "index", "values_col": numeric_cols[2] if len(numeric_cols) > 2 else "count"}
            ])
        else:  # Blank Canvas
            # Add quick dashboard charts similar to the Quick Dashboard section
            sampled_df = df.sample(min(5000, len(df))) if len(df) > 5000 else df  # Sample for performance
            
            # Numeric distributions
            if len(numeric_cols) > 0:
                dashboard_widgets.extend([
                    {"id": "kpi1", "type": "kpi", "title": "Total Records", "value": df.shape[0], "prev_value": 0},
                    {"id": "kpi2", "type": "kpi", "title": "Columns", "value": df.shape[1], "prev_value": 0},
                    {"id": "kpi3", "type": "kpi", "title": "Missing Values", "value": df.isnull().sum().sum(), "prev_value": 0},
                    {"id": "kpi4", "type": "kpi", "title": "Memory Usage", "value": round(df.memory_usage(deep=True).sum() / 1024, 2), "prev_value": 0},
                    {"id": "kpi5", "type": "kpi", "title": "Numeric Columns", "value": len(numeric_cols), "prev_value": 0},
                    {"id": "kpi6", "type": "kpi", "title": "Categorical Columns", "value": len(cat_cols), "prev_value": 0},
                    
                    # First 6 charts from quick dashboard
                    {"id": "chart1", "type": "bar_chart", "title": f"Distribution of {numeric_cols[0] if numeric_cols else 'Index'}", "x": df.index[:min(len(df), 10)], "y": numeric_cols[0] if numeric_cols else df.index[:min(len(df), 10)]},
                    {"id": "chart2", "type": "line_chart", "title": f"Trend of {numeric_cols[0] if numeric_cols else 'Index'}", "x": df.index[:min(len(df), 20)], "y": numeric_cols[0] if numeric_cols else df.index[:min(len(df), 20)]},
                    {"id": "chart3", "type": "correlation_heatmap", "title": "Correlation Matrix", "method": "pearson"},
                    {"id": "chart4", "type": "pie_chart", "title": f"Top {cat_cols[0] if cat_cols else 'Index'} Values", "col": cat_cols[0] if cat_cols else df.index.name or "index"},
                    {"id": "chart5", "type": "histogram", "title": f"Distribution of {numeric_cols[0] if numeric_cols else 'Index'}", "col": numeric_cols[0] if numeric_cols else df.index.name or "index"},
                    {"id": "chart6", "type": "scatter_plot", "title": f"Relationship: {numeric_cols[0] if numeric_cols else 'Var1'} vs {numeric_cols[1] if len(numeric_cols) > 1 else 'Var2'}", 
                     "x": numeric_cols[0] if numeric_cols else df.index.name or "index", 
                     "y": numeric_cols[1] if len(numeric_cols) > 1 else df.index.name or "index"},
                     
                     # Additional 6 charts
                    {"id": "chart7", "type": "treemap", "title": f"Treemap of {cat_cols[0] if cat_cols else 'Data'}", "path": [cat_cols[0]] if cat_cols else ["Index"], "values": numeric_cols[0] if numeric_cols else df.index.name or "value"},
                    {"id": "chart8", "type": "box_plot", "title": f"Box Plot of {numeric_cols[0] if numeric_cols else 'Data'}", "y": numeric_cols[0] if numeric_cols else df.index.name or "value", "x": cat_cols[0] if cat_cols else None},
                    {"id": "chart9", "type": "area_chart", "title": f"Area Chart of {numeric_cols[0] if numeric_cols else 'Data'}", "x": df.index[:min(len(df), 20)], "y": numeric_cols[0][:min(len(df), 20)] if numeric_cols else df.index[:min(len(df), 20)]},
                    {"id": "chart10", "type": "violin_plot", "title": f"Violin Plot of {numeric_cols[0] if numeric_cols else 'Data'}", "y": numeric_cols[0] if numeric_cols else df.index.name or "value", "x": cat_cols[0] if cat_cols else None},
                    {"id": "chart11", "type": "radar_chart", "title": f"Radar Chart of Top Variables", "vars": numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols},
                    {"id": "chart12", "type": "funnel_chart", "title": f"Funnel of {cat_cols[0] if cat_cols else 'Stages'}", "x": cat_cols[0] if cat_cols else ["Stage 1", "Stage 2", "Stage 3"], "y": numeric_cols[0] if numeric_cols else [100, 75, 50]},
                    
                    # Even more visuals
                    {"id": "chart13", "type": "waterfall_chart", "title": f"Change Analysis", "categories": ["Start", "Inc1", "Dec1", "Inc2", "End"], "values": [100, 20, -10, 15, 125]},
                    {"id": "chart14", "type": "gauge_chart", "title": f"Overall Metric", "value": df[numeric_cols[0]].mean() if numeric_cols else 50, "min_val": 0, "max_val": df[numeric_cols[0]].max() if numeric_cols else 100},
                    {"id": "chart15", "type": "parallel_coordinates", "title": f"Multivariate Analysis", "columns": numeric_cols[:min(5, len(numeric_cols))] if numeric_cols else ["Var1"]},
                    {"id": "chart16", "type": "sunburst", "title": f"Hierarchical Breakdown", "path": cat_cols[:3] if len(cat_cols) >= 3 else cat_cols if cat_cols else ["Level1", "Level2"], "values": numeric_cols[0] if numeric_cols else "count"},
                    {"id": "chart17", "type": "line_chart", "title": f"Time Series Analysis", "x": df.index[:min(len(df), 30)], "y": numeric_cols[1][:min(len(df), 30)] if len(numeric_cols) > 1 else df.index[:min(len(df), 30)]},
                    {"id": "chart18", "type": "correlation_heatmap", "title": f"Spearman Correlation", "method": "spearman"}
                ])
        
        # Store the dashboard in session state
        st.session_state[f'dashboard_{dashboard_title.replace(" ", "_")}'] = {
            'title': dashboard_title,
            'widgets': dashboard_widgets,
            'layout': layout_options,
            'template': template
        }
        
        # Set as active dashboard
        st.session_state['active_dashboard'] = dashboard_title
        st.success(f"Dashboard '{dashboard_title}' created with {len(dashboard_widgets)} widgets!")
        st.rerun()

    # Show the active dashboard if one exists
    if st.session_state.get('active_dashboard'):
        active_db_title = st.session_state['active_dashboard']
        dashboard_key = f'dashboard_{active_db_title.replace(" ", "_")}'
        current_dash = st.session_state.get(dashboard_key, {})
        
        if current_dash:
            st.subheader(f"Active Dashboard: {current_dash['title']}")
            
            # Display dashboard KPIs
            if any(w['type'] == 'kpi' for w in current_dash['widgets']):
                st.subheader("Key Performance Indicators")
                kpi_widgets = [w for w in current_dash['widgets'] if w['type'] == 'kpi']
                
                kpi_cols = st.columns(4)
                for i, kpi in enumerate(kpi_widgets[:4]):  # Show first 4 KPIs
                    with kpi_cols[i]:
                        delta = None
                        if kpi.get('prev_value') is not None and kpi['prev_value'] != 0:
                            delta_value = ((kpi['value'] - kpi['prev_value']) / abs(kpi['prev_value'])) * 100
                            delta = f"{delta_value:.1f}%"
                        
                        st.metric(
                            label=kpi['title'],
                            value=f"{kpi['value']:,.2f}" if isinstance(kpi['value'], (int, float)) else kpi['value'],
                            delta=delta
                        )
            
            # Display dashboard charts in a grid
            st.subheader("Visualizations")
            
            # Organize charts in a grid layout
            chart_widgets = [w for w in current_dash['widgets'] if w['type'] != 'kpi']
            
            # Create a grid of 2x2 for charts
            for i in range(0, len(chart_widgets), 2):
                cols = st.columns(2)
                
                # Left chart
                with cols[0]:
                    widget = chart_widgets[i]
                    try:
                        if widget['type'] == 'bar_chart':
                            fig = Visualizer.bar_chart(
                                df, 
                                x=widget['x'], 
                                y=widget['y'],
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'line_chart':
                            fig = Visualizer.line_chart(
                                pd.DataFrame({'x': widget['x'], 'y': widget['y']}), 
                                x='x', 
                                y='y',
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'pie_chart':
                            pie_data = df[widget['col']].value_counts().reset_index()
                            pie_data.columns = [widget['col'], 'count']
                            fig = Visualizer.pie_chart(
                                pie_data, 
                                names=widget['col'], 
                                values='count',
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'heatmap':
                            fig = Visualizer.correlation_heatmap(
                                df.select_dtypes(include=[np.number]), 
                                method=widget['method'],
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'area_chart':
                            df_temp = pd.DataFrame({'x': widget['x'], 'y': widget['y']})
                            fig = Visualizer.area_chart(
                                df_temp, 
                                x='x', 
                                y='y',
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'box_plot':
                            fig = Visualizer.box_plot(
                                df, 
                                y=widget['y'], 
                                x=widget['x'],
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'scatter_plot':
                            fig = Visualizer.scatter_plot(
                                df, 
                                x=widget['x'], 
                                y=widget['y'],
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'treemap':
                            fig = Visualizer.treemap(
                                df, 
                                path=widget['path'], 
                                values=widget['values'],
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'funnel_chart':
                            df_funnel = pd.DataFrame({'x': widget['x'], 'y': widget['y']})
                            fig = Visualizer.funnel_chart(
                                df_funnel, 
                                x='x', 
                                y='y',
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'gauge_chart':
                            fig = Visualizer.gauge_chart(
                                widget['value'], 
                                min_val=widget.get('min_val', 0), 
                                max_val=widget.get('max_val', 100),
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'correlation_heatmap':
                            fig = Visualizer.correlation_heatmap(
                                df.select_dtypes(include=[np.number]), 
                                method=widget['method'],
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        elif widget['type'] == 'histogram':
                            fig = Visualizer.histogram(
                                df, 
                                x=widget['col'],
                                title=widget['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error rendering {widget['type']}: {str(e)}")
                
                # Right chart if exists
                if i+1 < len(chart_widgets):
                    with cols[1]:
                        widget = chart_widgets[i+1]
                        try:
                            if widget['type'] == 'bar_chart':
                                fig = Visualizer.bar_chart(
                                    df, 
                                    x=widget['x'], 
                                    y=widget['y'],
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'line_chart':
                                df_temp = pd.DataFrame({'x': widget['x'], 'y': widget['y']})
                                fig = Visualizer.line_chart(
                                    df_temp, 
                                    x='x', 
                                    y='y',
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'pie_chart':
                                pie_data = df[widget['col']].value_counts().reset_index()
                                pie_data.columns = [widget['col'], 'count']
                                fig = Visualizer.pie_chart(
                                    pie_data, 
                                    names=widget['col'], 
                                    values='count',
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'heatmap':
                                fig = Visualizer.correlation_heatmap(
                                    df.select_dtypes(include=[np.number]), 
                                    method=widget['method'],
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'area_chart':
                                df_temp = pd.DataFrame({'x': widget['x'], 'y': widget['y']})
                                fig = Visualizer.area_chart(
                                    df_temp, 
                                    x='x', 
                                    y='y',
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'box_plot':
                                fig = Visualizer.box_plot(
                                    df, 
                                    y=widget['y'], 
                                    x=widget['x'],
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'scatter_plot':
                                fig = Visualizer.scatter_plot(
                                    df, 
                                    x=widget['x'], 
                                    y=widget['y'],
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'treemap':
                                fig = Visualizer.treemap(
                                    df, 
                                    path=widget['path'], 
                                    values=widget['values'],
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'funnel_chart':
                                df_funnel = pd.DataFrame({'x': widget['x'], 'y': widget['y']})
                                fig = Visualizer.funnel_chart(
                                    df_funnel, 
                                    x='x', 
                                    y='y',
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'gauge_chart':
                                fig = Visualizer.gauge_chart(
                                    widget['value'], 
                                    min_val=widget.get('min_val', 0), 
                                    max_val=widget.get('max_val', 100),
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'correlation_heatmap':
                                fig = Visualizer.correlation_heatmap(
                                    df.select_dtypes(include=[np.number]), 
                                    method=widget['method'],
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            elif widget['type'] == 'histogram':
                                fig = Visualizer.histogram(
                                    df, 
                                    x=widget['col'],
                                    title=widget['title']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error rendering {widget['type']}: {str(e)}")

# Quick Dashboard
with chart_builder_tab:
    render_section_header("Chart Builder", "Create interactive visualizations")

    chart_types = [
        "Bar Chart", "Line Chart", "Scatter Plot", "Histogram", 
        "Box Plot", "Violin Plot", "Pie Chart", "Area Chart",
        "Heatmap", "Treemap", "Sunburst", "Funnel Chart",
        "Waterfall Chart", "Gauge Chart", "Radar Chart", 
        "Parallel Coordinates", "Sankey Diagram"
    ]

    chart_type = st.selectbox("Chart Type", chart_types)

    # Add option for sampling large datasets for visualization
    sample_for_viz = st.checkbox("Sample large datasets for visualization", value=True, 
                                help="Automatically sample large datasets to improve visualization performance", key="viz_sample")
    max_viz_points = st.number_input("Max points for visualization", min_value=1000, max_value=50000, 
                                    value=10000, step=1000, 
                                    disabled=not sample_for_viz, key="viz_max_points")

    # Dynamic field selection based on chart type
    cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    if chart_type in ["Bar Chart", "Line Chart", "Area Chart"]:
        col1, col2, col3 = st.columns(3)
        with col1:
            x_col = st.selectbox("X Axis", cols)
        with col2:
            y_col = st.selectbox("Y Axis", numeric_cols if numeric_cols else cols)
        with col3:
            color_col = st.selectbox("Color (optional)", ["None"] + cat_cols)
            color_col = None if color_col == "None" else color_col

    elif chart_type == "Scatter Plot":
        col1, col2, col3 = st.columns(3)
        with col1:
            x_col = st.selectbox("X Axis", numeric_cols)
        with col2:
            y_col = st.selectbox("Y Axis", numeric_cols)
        with col3:
            color_col = st.selectbox("Color (optional)", ["None"] + cat_cols)
            color_col = None if color_col == "None" else color_col

    elif chart_type == "Histogram":
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("Column", numeric_cols)
        with col2:
            bins = st.slider("Bins", 5, 100, 20)

    elif chart_type == "Pie Chart":
        col1, col2 = st.columns(2)
        with col1:
            values_col = st.selectbox("Values", numeric_cols)
        with col2:
            names_col = st.selectbox("Names", cat_cols)

    elif chart_type == "Box Plot":
        col1, col2 = st.columns(2)
        with col1:
            y_col = st.selectbox("Y (Values)", numeric_cols)
        with col2:
            x_col = st.selectbox("X (Groups)", ["None"] + cat_cols)
            x_col = None if x_col == "None" else x_col

    elif chart_type == "Heatmap":
        corr_method = st.selectbox("Correlation Method", ["pearson", "spearman", "kendall"])

    elif chart_type == "Treemap":
        path_cols = st.multiselect("Path hierarchy", cat_cols, default=cat_cols[:2] if len(cat_cols) >= 2 else cat_cols)
        value_col = st.selectbox("Size", numeric_cols)

    elif chart_type == "Waterfall Chart":
        st.info("Waterfall chart requires categories and corresponding values.")
        categories = st.text_area("Categories (comma-separated)", value="Start,Increase 1,Decrease 1,Increase 2,End")
        values = st.text_area("Values (comma-separated numbers)", value="100,50,-30,20,140")
        title = st.text_input("Title", "Waterfall Chart Example")

    elif chart_type == "Gauge Chart":
        value_col = st.selectbox("Value Column", numeric_cols)
        min_val = float(df[value_col].min())
        max_val = float(df[value_col].max())
        gauge_min = st.number_input("Gauge Min", value=min_val)
        gauge_max = st.number_input("Gauge Max", value=max_val)

    elif chart_type in ["Radar Chart", "Parallel Coordinates"]:
        selected_cols = st.multiselect("Select numeric columns", numeric_cols, default=numeric_cols[:3])

    elif chart_type == "Sankey Diagram":
        st.info("Sankey diagram requires source, target, and value columns.")
        source_col = st.selectbox("Source Column", cat_cols if cat_cols else cols)
        target_col = st.selectbox("Target Column", cat_cols if cat_cols else cols)
        value_col = st.selectbox("Value Column", numeric_cols if numeric_cols else cols)

    if st.button("📊 Generate Chart", type="primary"):
        with st.spinner("Creating visualization..."):
            try:
                if chart_type == "Bar Chart":
                    fig = Visualizer.bar_chart(
                        df, x=x_col, y=y_col, color=color_col,
                        max_points=max_viz_points if sample_for_viz else len(df)
                    )
                elif chart_type == "Line Chart":
                    fig = Visualizer.line_chart(
                        df, x=x_col, y=y_col, color=color_col,
                        max_points=max_viz_points if sample_for_viz else len(df)
                    )
                elif chart_type == "Scatter Plot":
                    fig = Visualizer.scatter_plot(
                        df, x=x_col, y=y_col, color=color_col,
                        max_points=max_viz_points if sample_for_viz else len(df)
                    )
                elif chart_type == "Histogram":
                    fig = Visualizer.histogram(
                        df, x=x_col, nbins=bins,
                        max_points=max_viz_points if sample_for_viz else len(df)
                    )
                elif chart_type == "Box Plot":
                    fig = Visualizer.box_plot(
                        df, y=y_col, x=x_col,
                        max_points=max_viz_points if sample_for_viz else len(df)
                    )
                elif chart_type == "Pie Chart":
                    fig = Visualizer.pie_chart(
                        df, values=values_col, names=names_col
                    )
                elif chart_type == "Area Chart":
                    fig = Visualizer.area_chart(
                        df, x=x_col, y=y_col, color=color_col,
                        max_points=max_viz_points if sample_for_viz else len(df)
                    )
                elif chart_type == "Heatmap":
                    fig = Visualizer.correlation_heatmap(
                        df.select_dtypes(include=[np.number]),
                        method=corr_method,
                        max_points=max_viz_points if sample_for_viz else len(df)
                    )
                elif chart_type == "Treemap":
                    fig = Visualizer.treemap(
                        df, path=path_cols, values=value_col,
                        max_points=max_viz_points if sample_for_viz else len(df)
                    )
                elif chart_type == "Waterfall Chart":
                    cats = [cat.strip() for cat in categories.split(',')]
                    vals = [float(val.strip()) for val in values.split(',')]
                    fig = Visualizer.waterfall_chart(cats, vals, title=title)
                elif chart_type == "Gauge Chart":
                    avg_val = df[value_col].mean()
                    fig = Visualizer.gauge_chart(avg_val, min_val=gauge_min, max_val=gauge_max)
                elif chart_type == "Radar Chart":
                    fig = Visualizer.radar_chart(df, vars=selected_cols)
                elif chart_type == "Parallel Coordinates":
                    fig = Visualizer.parallel_coordinates(df[selected_cols])
                elif chart_type == "Sunburst":
                    fig = Visualizer.sunburst(df, path=path_cols, values=value_col,
                                             max_points=max_viz_points if sample_for_viz else len(df))
                elif chart_type == "Funnel Chart":
                    fig = Visualizer.funnel_chart(df, x=names_col, y=values_col,
                                                 max_points=max_viz_points if sample_for_viz else len(df))
                elif chart_type == "Violin Plot":
                    fig = Visualizer.violin_plot(df, y=y_col, x=x_col,
                                                max_points=max_viz_points if sample_for_viz else len(df))
                elif chart_type == "Sankey Diagram":
                    fig = Visualizer.sankey_diagram(df, source_col, target_col, value_col,
                                                   max_points=max_viz_points if sample_for_viz else len(df))

                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating chart: {str(e)}")

