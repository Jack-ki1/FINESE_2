"""
Navigation Component for data_all1
Provides enhanced navigation with breadcrumbs and quick jumps
"""
import streamlit as st
from typing import List, Dict, Optional


class NavigationManager:
    """Manages application navigation and page routing."""
    
    PAGES = {
        "Home": "data_all1.py",
        "Data Ingestion": "01_Data.py",
        "Exploratory Data Analysis": "02_EDA.py",
        "Data Cleaning": "03_Cleaning.py",
        "Visualization": "04_Visualization.py",
        "Statistical Analysis": "05_Analysis.py",
        "Machine Learning": "06_Modeling.py",
        "MLOps Center": "07_MLOps.py",
        "Report Generator": "08_Reports.py",
        "AI Assistant": "09_AI_Assistant.py"
    }
    
    @staticmethod
    def render_sidebar_navigation():
        """Render the enhanced sidebar navigation."""
        # Removed navigation section as requested
        pass
    
    @staticmethod
    def render_breadcrumbs():
        """Render breadcrumbs at the top of the page."""
        current_page = st.session_state.get("current_page", "data_all1.py")
        
        # Find the current page name
        current_page_name = "Home"
        for name, file in NavigationManager.PAGES.items():
            if file == current_page:
                current_page_name = name
                break
        
        st.markdown(
            f"<div style='margin-bottom: 20px; padding: 10px; background-color: var(--card-color); "
            f"border-radius: 5px; border-left: 4px solid var(--primary-color);'>"
            f"<small>You are here:</small><br>"
            f"<strong>{current_page_name}</strong>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    @staticmethod
    def get_current_page_name():
        """Get the name of the current page."""
        current_file = st.session_state.get("current_page", "data_all1.py")
        for name, file in NavigationManager.PAGES.items():
            if file == current_file:
                return name
        return "Home"


def render_enhanced_sidebar():
    """Render the enhanced sidebar with navigation and other components."""
    # Removed navigation section as requested
    pass