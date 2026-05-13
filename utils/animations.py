"""
Animation Utilities for FINESE2
Provides smooth transitions and loading animations
"""
import streamlit as st
import time
from typing import Callable, Any


class AnimationUtils:
    """Provides animation utilities for the application."""
    
    @staticmethod
    def animated_loader(text: str = "Processing...", duration: float = 2.0):
        """Display an animated loader with custom text."""
        placeholder = st.empty()
        
        # Define animation frames
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
        start_time = time.time()
        frame_idx = 0
        
        while time.time() - start_time < duration:
            frame = frames[frame_idx % len(frames)]
            placeholder.markdown(f"<div style='display:flex; align-items:center; justify-content:center; height:100px;'><span style='font-size:24px; margin-right:10px;'>{frame}</span> <span>{text}</span></div>", unsafe_allow_html=True)
            time.sleep(0.1)
            frame_idx += 1
        
        placeholder.empty()
    
    @staticmethod
    def fade_in_element(element_func: Callable, key: str = "fade_element"):
        """Display an element with a fade-in animation."""
        st.markdown(f"<div id='{key}' class='fade-in' style='opacity:0; animation:fadeIn 0.5s ease-in-out forwards;'></div>", unsafe_allow_html=True)
        element_func()
    
    @staticmethod
    def progress_with_animation(steps: list, process_func: Callable):
        """Show progress with animation for multi-step processes."""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(steps)
        
        for i, step in enumerate(steps):
            status_text.text(f"Processing: {step}...")
            progress_bar.progress((i + 1) / total_steps)
            
            # Simulate processing time - in real usage, this would be the actual processing
            process_func(step, i)
            
            time.sleep(0.2)  # Simulated processing delay
        
        status_text.success("Process completed!")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
    
    @staticmethod
    def slide_in_alert(message: str, level: str = "info", duration: float = 3.0):
        """Display a sliding alert message."""
        if level == "error":
            st.error(message)
        elif level == "warning":
            st.warning(message)
        elif level == "success":
            st.success(message)
        else:
            st.info(message)


def show_processing_animation(text: str = "Processing your data...", duration: float = 2.0):
    """Show a processing animation."""
    AnimationUtils.animated_loader(text, duration)


def animate_data_transition(before_df, after_df, operation_name: str = "Transformation"):
    """Animate the transition between two data states."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Before {operation_name}")
        st.dataframe(before_df, use_container_width=True, height=300)
    
    # Animation in the middle
    st.markdown("<div style='display:flex; align-items:center; justify-content:center; margin: 20px 0;'><h2>✨</h2></div>", unsafe_allow_html=True)
    
    with col2:
        st.subheader(f"After {operation_name}")
        st.dataframe(after_df, use_container_width=True, height=300)
    
    # Show differences
    st.subheader("Changes Summary")
    diff_rows = len(after_df) - len(before_df)
    diff_cols = len(after_df.columns) - len(before_df.columns)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"Row {operation_name}", f"{diff_rows:+d}")
    with col2:
        st.metric(f"Column {operation_name}", f"{diff_cols:+d}")