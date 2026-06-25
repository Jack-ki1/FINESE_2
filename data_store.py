import streamlit as st
import pandas as pd
from typing import Optional
from utils.ui_utils import log_change

class DataStore:
    @staticmethod
    def get_base_df() -> Optional[pd.DataFrame]:
        return st.session_state.get("base_df")
    
    @staticmethod
    def get_work_df() -> Optional[pd.DataFrame]:
        return st.session_state.get("work_df")
    
    @staticmethod
    def get_filtered_data() -> Optional[pd.DataFrame]:
        return st.session_state.get("filtered_data")
    
    @staticmethod
    def update_base_df(df: pd.DataFrame) -> None:
        st.session_state.base_df = df
        # Also update work_df when base_df changes
        st.session_state.work_df = df.copy()
        # Invalidate cached data
        st.session_state.filtered_data = None
        st.session_state.cached_data_health = None
        log_change("Updated base data", f"Shape: {df.shape}")
    
    @staticmethod
    def update_work_df(df: pd.DataFrame, reason: str = "") -> None:
        st.session_state.work_df = df
        # Invalidate dependent caches
        st.session_state.filtered_data = None
        st.session_state.cached_data_health = None
        if reason:
            log_change(reason)
    
    @staticmethod
    def apply_transform(fn, description: str) -> bool:
        """Apply a transform function to work_df with full cache invalidation."""
        df = DataStore.get_work_df()
        if df is None:
            return False
        try:
            result = fn(df.copy())
            DataStore.update_work_df(result, description)
            return True
        except Exception as e:
            st.error(f"Transform failed: {e}")
            return False