def format_number(num):
    """Format numbers with appropriate units."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)
"""
Custom Styling and Theme Utilities for data_all1
"""
import streamlit as st


def render_metric_card(title: str, value: str, description: str = "", icon: str = "📊"):
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 2.5rem; color: #00D4AA; margin-bottom: 0.5rem;">{icon}</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #FAFAFA; margin-bottom: 0.25rem;">{value}</div>
        <div style="font-size: 0.9rem; color: #888;">{title}</div>
        {f'<div style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">{description}</div>' if description else ''}
    </div>
    """, unsafe_allow_html=True)

def render_section_header(title: str, description: str = ""):
    """Render a styled section header."""
    st.markdown(f"""
    <div style="margin: 2rem 0 1rem 0;">
        <h2 style="margin: 0;">{title}</h2>
        <p style="color: #888; margin-top: 0.5rem;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def render_status_badge(status: str, message: str):
    """Render a status badge with appropriate styling."""
    status_classes = {
        "success": "status-success",
        "warning": "status-warning", 
        "error": "status-error",
        "info": "status-info"
    }
    
    status_class = status_classes.get(status, "status-info")
    
    st.markdown(f"""
    <span class="{status_class}">
        {status.upper()}: {message}
    </span>
    """, unsafe_allow_html=True)
