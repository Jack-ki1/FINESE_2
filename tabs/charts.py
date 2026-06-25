import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union
import logging
from io import BytesIO
from datetime import datetime
import zipfile
import plotly.graph_objects as go
import plotly.express as px
from plotly.io import templates

# Plotly static image export requires Kaleido
try:
    import kaleido  # noqa: F401
    KALEIDO_AVAILABLE = True
except Exception:
    KALEIDO_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import core components
from core.dataset_context import DatasetContext

# Import shared utilities and config
from utils import get_numeric_columns, get_categorical_columns
from config import BRAND_NAME, SECTION_HEADER_CLASS, SECTION_SUBHEADER_CLASS, EXPORT_DATE_FORMAT

CHART_TYPES = [
    "Bar", "Line", "Scatter", "Histogram", "Box", "Area",
    "Pie", "Violin", "Heatmap", "Density Contour", "Sunburst", "Treemap"
]

CHART_CONFIG = {
    "Bar": {"required": ["x", "y"], "optional": ["color"], "x_type": "any", "y_type": "numeric"},
    "Line": {"required": ["x", "y"], "optional": ["color"], "x_type": "any", "y_type": "numeric"},
    "Scatter": {"required": ["x", "y"], "optional": ["color", "size"], "x_type": "numeric", "y_type": "numeric"},
    "Histogram": {"required": ["x"], "optional": ["color"], "x_type": "numeric", "y_type": None},
    "Box": {"required": ["x", "y"], "optional": ["color"], "x_type": "any", "y_type": "numeric"},
    "Area": {"required": ["x", "y"], "optional": ["color"], "x_type": "any", "y_type": "numeric"},
    "Pie": {"required": ["x"], "optional": [], "x_type": "any", "y_type": None},
    "Violin": {"required": ["x", "y"], "optional": ["color"], "x_type": "any", "y_type": "numeric"},
    "Heatmap": {"required": ["x", "y"], "optional": ["color"], "x_type": "any", "y_type": "numeric"},
    "Density Contour": {"required": ["x", "y"], "optional": ["color"], "x_type": "numeric", "y_type": "numeric"},
    "Sunburst": {"required": ["path"], "optional": ["values"], "x_type": "any", "y_type": None},
    "Treemap": {"required": ["path"], "optional": ["values"], "x_type": "any", "y_type": None},
}

def render_charts_tab(dataset_context: DatasetContext) -> None:
    """
    Unified Charts & Pivot Tab: Build pivot tables and interactive visualizations in one place.
    """
    if dataset_context is None or dataset_context.filtered_df.empty:
        st.warning("⚠️ No data available. Please load or filter data first.")
        return

    filtered = dataset_context.filtered_df
    
    st.markdown(f'<div class="{SECTION_HEADER_CLASS}">📊 Charts & Pivot Studio</div>', unsafe_allow_html=True)
    st.caption("Aggregate with pivot tables or visualize with interactive charts — all in one workflow.")

    # --- Main Navigation ---
    viz_mode = st.radio(
        "Choose your analysis style:",
        ["📈 Interactive Charts", "📊 Pivot Tables"],
        horizontal=True,
        key="charts_pivot_mode"
    )

    if viz_mode == "📈 Interactive Charts":
        _render_chart_builder(filtered)
    else:
        _render_pivot_builder(filtered)

# =============== CHART BUILDER (from chart_builder.py) ===============
def _suggest_axis(df: pd.DataFrame, axis: str, chart_type: str, current_value: Optional[str]) -> Optional[str]:
    if current_value and current_value in df.columns:
        return current_value
    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)
    if chart_type in ["Pie", "Sunburst", "Treemap"]:
        return cat_cols[0] if cat_cols else (num_cols[0] if num_cols else None)
    if chart_type == "Histogram":
        return num_cols[0] if num_cols else None
    if chart_type in ["Density Contour", "Scatter"]:
        if axis == "x":
            return num_cols[0] if len(num_cols) >= 1 else None
        elif axis == "y":
            return num_cols[1] if len(num_cols) >= 2 else (num_cols[0] if num_cols else None)
    if chart_type in ["Bar", "Line", "Area", "Box", "Violin", "Heatmap"]:
        if axis == "x":
            return cat_cols[0] if cat_cols else (num_cols[0] if num_cols else None)
        elif axis == "y":
            return num_cols[0] if num_cols else None
    if axis == "x":
        return cat_cols[0] if cat_cols else (num_cols[0] if num_cols else None)
    elif axis == "y":
        return num_cols[0] if num_cols else None
    return None

def _validate_config(chart_type: str, x: str, y: str, color: str, path: list, size: str, df: pd.DataFrame) -> bool:
    if chart_type not in CHART_CONFIG:
        return False
    config = CHART_CONFIG[chart_type]
    for req in config["required"]:
        val = None
        if req == "x": val = x
        elif req == "y": val = y
        elif req == "path": val = path
        if val is None:
            return False
    if config["x_type"] == "numeric" and x and not pd.api.types.is_numeric_dtype(df[x]):
        return False
    if config["y_type"] == "numeric" and y and not pd.api.types.is_numeric_dtype(df[y]):
        return False
    if chart_type == "Pie" and y is not None:
        return False
    if chart_type in ["Sunburst", "Treemap"]:
        if not isinstance(path, list) or len(path) == 0:
            return False
        for p in path:
            if p not in df.columns or not pd.api.types.is_object_dtype(df[p]):
                return False
    if size and chart_type != "Scatter":
        return False
    if color and color not in df.columns:
        return False
    return True

#########################
def _create_plotly_figure(df: pd.DataFrame, cfg: Dict, theme: str) -> go.Figure:
    # Lazy import to ensure this function doesn't force module-level imports
    import plotly.express as px
    import plotly.graph_objects as go

    t = cfg["type"]
    x, y, color, size, path = cfg["x"], cfg["y"], cfg["color"], cfg["size"], cfg["path"]
    fig = None
    if t == "Bar":
        fig = px.bar(df, x=x, y=y, color=color)
    elif t == "Line":
        fig = px.line(df, x=x, y=y, color=color)
    elif t == "Scatter":
        fig = px.scatter(df, x=x, y=y, color=color, size=size)
    elif t == "Histogram":
        fig = px.histogram(df, x=x, color=color)
    elif t == "Box":
        fig = px.box(df, x=x, y=y, color=color)
    elif t == "Area":
        fig = px.area(df, x=x, y=y, color=color)
    elif t == "Pie":
        counts = df[x].astype(str).value_counts().reset_index()
        counts.columns = [x, "count"]
        fig = px.pie(counts, names=x, values="count")
    elif t == "Violin":
        fig = px.violin(df, x=x, y=y, color=color)
    elif t == "Heatmap":
        pivot = df.pivot_table(values=y, index=x, columns=color, aggfunc="mean", dropna=True)
        fig = px.imshow(pivot, aspect="auto")
    elif t == "Density Contour":
        fig = px.density_contour(df, x=x, y=y, color=color)
    elif t == "Sunburst":
        fig = px.sunburst(df, path=path)
    elif t == "Treemap":
        fig = px.treemap(df, path=path)
    else:
        raise ValueError(f"Unsupported chart type: {t}")

    # Normalize/validate theme -> fall back to 'plotly' if invalid
    def _normalize_template(name: Optional[str]) -> str:
        if not name:
            return "plotly"
        name_lower = str(name).lower()
        mapping = {
            "light": "plotly_white",
            "white": "plotly_white",
            "dark": "plotly_dark",
            "ggplot": "ggplot2",
        }
        candidate = mapping.get(name_lower, name)
        # If candidate is a compound of registered templates, keep only valid parts
        if "+" in candidate:
            try:
                # Access templates correctly
                template_names = list(templates)
                parts = [p for p in candidate.split("+") if p in template_names]
                if parts:
                    return "+".join(parts)
            except Exception:
                pass
        # If exact match in registered templates, use it
        try:
            # Access templates correctly
            template_names = list(templates)
            if candidate in template_names:
                return candidate
            # otherwise try lowercase match
            for tpl in template_names:
                if tpl.lower() == str(candidate).lower():
                    return tpl
        except Exception:
            pass
        # fallback
        return "plotly"

    valid_template = _normalize_template(theme)
    fig.update_layout(template=valid_template)
    return fig

##################################
def _render_chart_builder(filtered: pd.DataFrame) -> None:
    with st.expander("⚙️ Advanced Settings", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            n_charts = st.slider("Number of Charts", 1, 6, 2, 1, key="n_charts")
        with col2:
            layout_cols = st.selectbox("Layout Columns", [1, 2, 3], index=1, key="layout_cols")
        show_titles = st.checkbox("Show Chart Titles", value=True, key="show_titles")
        theme = st.selectbox("Plot Theme", ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn"], index=0, key="theme")

    if "charts" not in st.session_state:
        st.session_state.charts = []
    while len(st.session_state.charts) < n_charts:
        st.session_state.charts.append({"type": "Bar", "x": None, "y": None, "color": None, "size": None, "path": None, "title": ""})
    while len(st.session_state.charts) > n_charts:
        st.session_state.charts.pop()

    # Chart configuration
    st.markdown("### 🛠️ Chart Configuration")
    for i in range(n_charts):
        with st.container():
            st.markdown(f"#### 📊 Chart {i+1}")
            cfg = st.session_state.charts[i]
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                chart_type = st.selectbox(
                    f"Chart Type",
                    CHART_TYPES,
                    index=CHART_TYPES.index(cfg["type"]) if cfg["type"] in CHART_TYPES else 0,
                    key=f"type_{i}"
                )
            with col2:
                x_col = _suggest_axis(filtered, "x", chart_type, cfg.get("x"))
                x_options = [""] + list(filtered.columns)
                x = st.selectbox(f"X-Axis", x_options, index=x_options.index(x_col) if x_col in x_options else 0, key=f"x_{i}")
                if x == "": x = None
            with col3:
                y_options = [""] + get_numeric_columns(filtered)
                y_col = _suggest_axis(filtered, "y", chart_type, cfg.get("y"))
                y = st.selectbox(f"Y-Axis", y_options, index=y_options.index(y_col) if y_col in y_options else 0, key=f"y_{i}")
                if y == "": y = None

            color_options = [""] + list(filtered.columns)
            color = st.selectbox(
                f"Color By",
                color_options,
                index=color_options.index(cfg.get("color")) if cfg.get("color") in color_options else 0,
                key=f"color_{i}"
            )
            if color == "": color = None

            size = None
            if chart_type == "Scatter":
                size_options = [""] + get_numeric_columns(filtered)
                size = st.selectbox(f"Size By", size_options, index=size_options.index(cfg.get("size")) if cfg.get("size") in size_options else 0, key=f"size_{i}")
                if size == "": size = None

            path = None
            if chart_type in ["Sunburst", "Treemap"]:
                path_options = get_categorical_columns(filtered)
                path = st.multiselect(f"Path", path_options, default=cfg.get("path"), key=f"path_{i}")
                if len(path) == 0: path = None

            title = st.text_input(f"Chart Title", value=cfg.get("title", ""), key=f"title_{i}")

            # Validate and store config
            valid = _validate_config(chart_type, x, y, color, path, size, filtered)
            st.session_state.charts[i] = {
                "type": chart_type,
                "x": x,
                "y": y,
                "color": color,
                "size": size,
                "path": path,
                "title": title,
                "valid": valid
            }

    # Display charts
    st.markdown("---")
    st.markdown("### 🖼️ Generated Charts")
    
    for i in range(0, len(st.session_state.charts), layout_cols):
        cols = st.columns(layout_cols)
        for j in range(layout_cols):
            idx = i + j
            if idx >= len(st.session_state.charts):
                break
            cfg = st.session_state.charts[idx]
            with cols[j]:
                if cfg["valid"]:
                    try:
                        fig = _create_plotly_figure(filtered, cfg, theme)
                        if show_titles and cfg["title"]:
                            fig.update_layout(title=cfg["title"])
                        st.plotly_chart(fig, use_container_width=True, key=f"fig_{idx}")
                        
                        # Add export button for individual charts (requires Kaleido)
                        if KALEIDO_AVAILABLE:
                            buf = BytesIO()
                            fig.write_image(buf, format="png")
                            st.download_button(
                                label="💾 Save Chart",
                                data=buf.getvalue(),
                                file_name=f"{BRAND_NAME.lower()}_chart_{idx+1}_{datetime.now().strftime(EXPORT_DATE_FORMAT)}.png",
                                mime="image/png",
                                key=f"export_chart_{idx}"
                            )
                        else:
                            st.info("Static PNG export requires Kaleido. Install `kaleido` to enable this button.")
                    except Exception as e:
                        logger.error(f"Chart {idx} render error: {e}")
                        st.error(f"❌ Chart failed: {str(e)}")
                else:
                    st.info("🔧 Fix configuration above.")

    # Export all charts
    st.markdown("---")
    st.markdown("### 📥 Export All Charts")
    if st.button("🖼️ Download All Charts as PNG", type="primary"):
        if not KALEIDO_AVAILABLE:
            st.info("Static PNG export requires Kaleido. Install `kaleido` to enable this bulk download.")
            return

        png_buffers = []
        for i, cfg in enumerate(st.session_state.charts):
            if cfg["valid"]:
                try:
                    fig = _create_plotly_figure(filtered, cfg, theme)
                    if show_titles and cfg["title"]:
                        fig.update_layout(title=cfg["title"])
                    img_bytes = fig.to_image(format="png", width=800, height=500)
                    png_buffers.append((f"chart_{i+1}_{cfg['type']}.png", img_bytes))
                except Exception as e:
                    logger.error(f"Chart {i} export error: {e}")
                    st.warning(f"⚠️ Failed to export chart {i+1}: {str(e)}")

        if png_buffers:
            # Create ZIP file
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for filename, data in png_buffers:
                    zip_file.writestr(filename, data)
            zip_buffer.seek(0)

            st.success("✅ All charts exported successfully!")
            st.download_button(
                label="⬇️ Download Charts (.zip)",
                data=zip_buffer.getvalue(),
                file_name=f"{BRAND_NAME.lower()}_charts_{datetime.now().strftime(EXPORT_DATE_FORMAT)}.zip",
                mime="application/zip",
                key="download_all_charts"
            )
        else:
            st.info("No valid charts to export.")

def _render_pivot_builder(filtered: pd.DataFrame) -> None:
    st.markdown("### 📊 Pivot Table Builder")
    
    if filtered is None or filtered.empty:
        st.warning("⚠️ No data available for pivot table.")
        return
    
    # Select columns for pivot
    all_cols = list(filtered.columns)
    
    # Index selection
    index_cols = st.multiselect("Select Row Index", all_cols, key="pivot_index")
    
    # Column selection
    column_cols = st.multiselect("Select Column Index", [col for col in all_cols if col not in index_cols], key="pivot_columns")
    
    # Value selection
    numeric_cols = get_numeric_columns(filtered)
    value_cols = st.multiselect("Select Values", numeric_cols, key="pivot_values")
    
    # Aggregation function
    agg_funcs = ["sum", "mean", "count", "min", "max", "std"]
    agg_func = st.selectbox("Select Aggregation Function", agg_funcs, key="pivot_agg")
    
    # Create pivot table
    if st.button("📊 Generate Pivot Table", type="primary") and index_cols and value_cols:
        try:
            pivot_table = pd.pivot_table(
                filtered,
                index=index_cols if len(index_cols) > 1 else index_cols[0],
                columns=column_cols if column_cols else None,
                values=value_cols if len(value_cols) > 1 else value_cols[0],
                aggfunc=agg_func,
                fill_value=0
            )
            
            st.markdown("### 📈 Generated Pivot Table")
            st.dataframe(pivot_table, use_container_width=True)
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download as CSV",
                    data=pivot_table.to_csv(),
                    file_name=f"{BRAND_NAME.lower()}_pivot_{datetime.now().strftime(EXPORT_DATE_FORMAT)}.csv",
                    mime="text/csv",
                    key="download_pivot_csv"
                )
            with col2:
                # Convert to Excel
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    pivot_table.to_excel(writer, sheet_name='PivotTable')
                st.download_button(
                    label="📥 Download as Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"{BRAND_NAME.lower()}_pivot_{datetime.now().strftime(EXPORT_DATE_FORMAT)}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_pivot_excel"
                )
                
        except Exception as e:
            logger.error(f"Pivot table creation error: {e}")
            st.error(f"❌ Failed to create pivot table: {str(e)}")
    elif not (index_cols and value_cols):
        st.info("👆 Select at least one row index and one value column to generate a pivot table.")