import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
from io import BytesIO

class DataAccessLayer:
    """
    Provides controlled access to data in session state to prevent direct manipulation
    that could lead to inconsistent state.
    """
    
    @staticmethod
    def get_dataframe(name: str) -> Optional[pd.DataFrame]:
        """Get a dataframe by name from session state safely."""
        if name not in ["base_df", "work_df", "filtered_data"]:
            raise ValueError(f"Invalid dataframe name: {name}")
        return st.session_state.get(name)
    
    @staticmethod
    def set_dataframe(name: str, df: pd.DataFrame) -> None:
        """Safely set a dataframe in session state with cache invalidation."""
        if name not in ["base_df", "work_df"]:
            raise ValueError(f"Invalid dataframe name: {name}")
        
        # Set the dataframe
        st.session_state[name] = df.copy()
        
        # Invalidate dependent caches
        if name == "base_df":
            st.session_state["work_df"] = df.copy()
        
        # Always invalidate filtered data when base/work data changes
        st.session_state["filtered_data"] = None
        st.session_state["cached_data_health"] = None
        
        # Clear model-related states when data changes
        if name in ["base_df", "work_df"]:
            for key in ["pipeline", "leaderboard", "unsupervised_model", "cluster_labels"]:
                if key in st.session_state:
                    del st.session_state[key]
    
    @staticmethod
    def get_state(key: str, default: Any = None) -> Any:
        """Safely get a value from session state."""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set_state(key: str, value: Any) -> None:
        """Safely set a value in session state."""
        st.session_state[key] = value
    
    @staticmethod
    def invalidate_cache() -> None:
        """Invalidate all cached data."""
        for key in ["filtered_data", "cached_data_health"]:
            if key in st.session_state:
                st.session_state[key] = None
    
    @staticmethod
    def get_available_datasets() -> List[str]:
        """Get list of available dataset names in session state."""
        datasets = []
        if st.session_state.get("base_df") is not None:
            datasets.append("Original Dataset")
        if st.session_state.get("work_df") is not None:
            datasets.append("Working Dataset")
        if st.session_state.get("filtered_data") is not None:
            datasets.append("Filtered Dataset")
        return datasets