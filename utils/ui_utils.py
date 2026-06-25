import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def create_kpis(df: pd.DataFrame) -> None:
    """Create KPI cards showing dataset health metrics."""
    if df.empty:
        st.warning("No data to display KPIs for")
        return
    
    # Calculate metrics
    total_rows = len(df)
    total_cols = len(df.columns)
    missing_cells = df.isnull().sum().sum()
    missing_pct = (missing_cells / (total_rows * total_cols)) * 100 if total_rows > 0 and total_cols > 0 else 0
    duplicate_rows = df.duplicated().sum()
    memory_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
    
    # Create KPI cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        st.metric(
            label="📊 Rows",
            value=f"{total_rows:,}",
            delta=None
        )
    
    with kpi2:
        st.metric(
            label="📈 Cols", 
            value=f"{total_cols}",
            delta=None
        )
    
    with kpi3:
        st.metric(
            label="❌ Missing (%)",
            value=f"{missing_pct:.1f}%",
            delta=None
        )
    
    with kpi4:
        st.metric(
            label="🔄 Duplicates", 
            value=f"{duplicate_rows:,}",
            delta=None
        )
    
    with kpi5:
        st.metric(
            label="💾 Memory (MB)",
            value=f"{memory_usage:.1f} MB",
            delta=None
        )

def log_change(operation: str, details: str = "") -> None:
    """Log a change to the change log in session state."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {operation}"
    if details:
        entry += f" ({details})"
    
    # Maintain only the last 20 log entries to prevent excessive memory usage
    if "change_log" not in st.session_state:
        st.session_state.change_log = []
    
    st.session_state.change_log.append(entry)
    
    # Keep only last 20 entries
    if len(st.session_state.change_log) > 20:
        st.session_state.change_log = st.session_state.change_log[-20:]
    
    # Also log to Python logger
    logger.info(f"Change logged: {entry}")

def reset_app() -> None:
    """
    Reset all application state to initial empty state.
    Clears base_df, work_df, resets flags, and triggers rerun.
    """
    try:
        # Explicitly delete DataFrames to free memory
        if 'base_df' in st.session_state and st.session_state.base_df is not None:
            del st.session_state.base_df
        if 'work_df' in st.session_state and st.session_state.work_df is not None:
            del st.session_state.work_df
        if 'filtered_data' in st.session_state and st.session_state.filtered_data is not None:
            del st.session_state.filtered_data
            
        st.session_state.base_df = None
        st.session_state.work_df = None
        st.session_state.filtered_data = None
        st.session_state.data_loaded = False
        st.session_state.change_log = []
        
        # Reset ML-related states
        ml_states = [
            'pipeline', 'target_col', 'problem_type', 'selected_features', 
            'learning_type', 'leaderboard', 'encoding_method', 'scaling_method',
            'missing_value_strategy', 'n_clusters', 'clustering_algo', 'unsupervised_task'
        ]
        
        for state in ml_states:
            if state in st.session_state:
                del st.session_state[state]
        
        # Reset chatbot states
        if 'chat_history' in st.session_state:
            st.session_state.chat_history = []
        
        # Reset filter states
        filter_keys = [k for k in st.session_state.keys() if k.startswith('filter_') or k.startswith('slider_')]
        for key in filter_keys:
            del st.session_state[key]
        
        # Reset cached states
        cache_keys = ['filtered_data_key', 'cached_data_health']
        for key in cache_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        st.rerun()
    except Exception as e:
        logger.error(f"Error during app reset: {e}")
        # Fallback: refresh the page
        st.rerun()

def display_change_log() -> None:
    """Display the change log in the UI."""
    if "change_log" in st.session_state and st.session_state.change_log:
        with st.expander("📝 Recent Actions", expanded=False):
            for entry in reversed(st.session_state.change_log):
                st.caption(f"`{entry}`")
    else:
        st.info("No actions logged yet")

def dataframe_preview(
    df: pd.DataFrame,
    title: str,
    n: int = 10,
    head: bool = True,
    hide_index: bool = False,
) -> None:
    """Render a small dataframe preview in a consistent way."""
    if df is None or df.empty:
        st.info(f"{title}: no data")
        return
    st.subheader(title)
    preview = df.head(n) if head else df.tail(n)
    st.dataframe(preview, use_container_width=True, hide_index=hide_index)


def show_data_overview(df: pd.DataFrame) -> None:
    """Show an overview of the dataframe."""
    if df.empty:
        st.warning("No data to display overview for")
        return
    
    st.markdown("### 📋 Data Overview")
    
    # Shape info
    shape_info = pd.DataFrame({
        'Rows': [len(df)],
        'Columns': [len(df.columns)],
        'Cells': [df.size],
        'Memory Usage (MB)': [df.memory_usage(deep=True).sum() / (1024 * 1024)]
    })
    st.dataframe(shape_info, use_container_width=True)
    
    # Data types
    st.markdown("#### Column Types")
    dtype_counts = df.dtypes.value_counts()
    dtype_df = pd.DataFrame({
        'Type': dtype_counts.index.astype(str),
        'Count': dtype_counts.values
    })
    st.dataframe(dtype_df, use_container_width=True)
    
    # Sample of data
    st.markdown("#### Sample Data (First 5 rows)")
    st.dataframe(df.head(), use_container_width=True)

# -----------------------------
# UI Primitives (Reusable Helpers)
# -----------------------------

def render_section_header(title: str) -> None:
    """
    Render a consistent section header across the dashboard.
    Uses SECTION_HEADER_CLASS from config.
    """
    try:
        from config import SECTION_HEADER_CLASS
        st.markdown(f'<div class="{SECTION_HEADER_CLASS}">{title}</div>', unsafe_allow_html=True)
    except Exception:
        # Fallback: simple markdown if config import fails for any reason
        st.subheader(title)

def render_section_subheader(subtitle: str) -> None:
    """
    Render a consistent section subheader across the dashboard.
    Uses SECTION_SUBHEADER_CLASS from config.
    """
    try:
        from config import SECTION_SUBHEADER_CLASS
        st.markdown(f'<div class="{SECTION_SUBHEADER_CLASS}">{subtitle}</div>', unsafe_allow_html=True)
    except Exception:
        st.caption(subtitle)

def expander_block(label: str, default_expanded: bool = False, *, icon: Optional[str] = None):
    """
    Wrapper for st.expander to keep expander usage consistent.
    Returns the context manager from st.expander.
    """
    if icon:
        label = f"{icon} {label}"
    return st.expander(label, expanded=default_expanded)

def card_container(title: Optional[str] = None):
    """
    Create a simple Streamlit container that is styled as a 'card' via CSS.
    Usage:
        with card_container("My Card"):
            ...
    """
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if title:
        st.markdown(f'<div class="card-header">{title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-body">', unsafe_allow_html=True)

def end_card_container():
    """Close the card container started by card_container()."""
    st.markdown('</div></div>', unsafe_allow_html=True)

# Convenience context manager-like pattern:
# Since Streamlit doesn't offer real HTML context manager hooks, callers can do:
#   st.markdown('<div class="card">...') style,
# but we also provide the simplest safe pattern below:
class _CardCtx:
    def __init__(self, title: Optional[str]):
        self.title = title

    def __enter__(self):
        card_container(self.title)
        return self

    def __exit__(self, exc_type, exc, tb):
        end_card_container()
        return False

def card(title: Optional[str] = None):
    """Context manager for a styled card."""
    return _CardCtx(title)

def expandable_data_block(
    label: str,
    df: pd.DataFrame,
    *,
    n: int = 10,
    head: bool = True,
    hide_index: bool = False,
    default_expanded: bool = False
) -> None:
    """
    Render a dataframe preview inside an expander using the same preview format.
    """
    if df is None or df.empty:
        return

    with st.expander(label, expanded=default_expanded):
        preview = df.head(n) if head else df.tail(n)
        st.dataframe(preview, use_container_width=True, hide_index=hide_index)
