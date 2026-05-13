"""
FINESE2 - Data Intelligence Platform
Main entry point and home dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np
import datetime
from datetime import datetime as dt
import base64

# Must be first Streamlit command
st.set_page_config(
    page_title="FINESE2 | Data Intelligence Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.session_state import SessionManager
from utils.styling import render_metric_card, render_section_header, render_status_badge
from utils.notifications import render_notification_center
from utils.search import render_search_bar
from utils.helpers import summarize_dataframe, format_number
from modules.data_manager import DataManager
from modules.ai_assistant import render_ai_settings_sidebar



# Initialize session
SessionManager.init()

# Set current page in session state
st.session_state.current_page = "FINESE2.py"


# Render notification center in sidebar
render_notification_center()

# Render search bar in sidebar
render_search_bar()

# Activity Log
activities = SessionManager.get_activity_log()[-5:]  # Get last 5 activities

with st.sidebar:
    st.markdown("### Recent Activity")
    if activities:
        for activity in activities:
            st.caption(f"• {activity}")
    else:
        st.caption("No activity yet")

# =============== HEADER ===============
now_str = dt.now().strftime("%b %d, %Y · %H:%M")

# Function to convert image to base64 - simplified for Hugging Face
def get_image_as_base64(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None


# Path to your logo image - use relative path for Hugging Face
logo_path = "logo.png"
logo_base64 = get_image_as_base64(logo_path)

if logo_base64:
    logo_url = f"data:image/png;base64,{logo_base64}"
else:
    # Fallback to default logo or placeholder
    logo_url = "https://placehold.co/40x40/png"  # Placeholder image

st.markdown(f"""
<div class="header">
  <div class="brand">
    <div class="logo"><img src="{logo_url}" alt="logo" width="32" height="32"></div>
    <div>
      <div class="title">FINESE · Smart Data Explorer Pro</div>
      <div class="subtitle">Fast insights • Clean visuals • Board-ready reports</div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-weight:700;">{now_str}</div>
    <div style="opacity:.8;">Today</div>
  </div>
</div>
""", unsafe_allow_html=True)


# Feature Cards
render_section_header("Platform Capabilities", "Everything you need for end-to-end data intelligence")

cols = st.columns(5)
features = [
    ("📁", "Data Ingestion", "CSV, Excel, JSON, Parquet, SQL databases, and more. Auto-detect types."),
    ("🔍", "Auto EDA", "ydata-profiling, Sweetviz, correlation analysis, and data quality reports."),
    ("🧹", "Smart Cleaning", "Missing values, outliers, duplicates, scaling, encoding — with recommendations."),
    ("📊", "Visualization", "15+ interactive chart types. Dashboard builder. Export-ready plots."),
    ("📈", "Statistical Analysis", "Hypothesis testing, regression, ANOVA, chi-square, normality tests."),
    ("🤖", "Auto ML", "Classification, regression, clustering. Model comparison. Feature importance."),
    ("⚙️", "MLOps", "Experiment tracking, model registry, leaderboards, run comparison."),
    ("📝", "Reports", "HTML, Excel, Word, Markdown exports. Professional templates."),
    ("💬", "AI Assistant", "Multi-provider LLM support. Claude, GPT, Gemini, Ollama, and more."),
]

for i, (icon, title, desc) in enumerate(features):
    with cols[i % 5]:
        st.markdown(f"""
        <div class="metric-card" style="min-height: 180px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">{icon}</div>
            <div style="font-weight: 600; color: #FAFAFA; margin-bottom: 8px;">{title}</div>
            <div style="font-size: 0.8rem; color: #888; line-height: 1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

# Quick Start
render_section_header("Quick Start", "click on any section in the sidebar to begin your data journey")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 1.2rem; font-weight: 600; color: #00D4AA; margin-bottom: 10px;">1.  Data</div>
        <p style="color: #888; font-size: 0.9rem;">Upload CSV, Excel, or connect to a database. Use sample data to explore.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 1.2rem; font-weight: 600; color: #00D4AA; margin-bottom: 10px;">2. Explore & Clean</div>
        <p style="color: #888; font-size: 0.9rem;">Run automated EDA, apply smart cleaning recommendations, visualize patterns.</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 1.2rem; font-weight: 600; color: #00D4AA; margin-bottom: 10px;">3. Model & Report</div>
        <p style="color: #888; font-size: 0.9rem;">Train ML models, track experiments, generate reports, and consult AI for insights.</p>
    </div>
    """, unsafe_allow_html=True)
