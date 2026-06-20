"""
Session State Manager for FINESE2
Enhanced with comprehensive notification system and activity logging
"""
import streamlit as st
import pandas as pd
from typing import Any, Dict, Optional, List
from copy import deepcopy
import numpy as np
import copy
import json
from datetime import datetime

class SessionManager:
    """Manages all session state variables with type safety and defaults."""
    
    # Default values for session state variables
    DEFAULTS = {
        # Data
        "raw_df": None,
        "cleaned_df": None,
        "current_df": None,
        "data_source": None,
        "file_name": None,
        "history": [],      # For undo/redo functionality
        "future": [],       # For redo functionality
        "history_limit": 20,  # Increased history limit for better undo/redo

        # EDA
        "eda_report": None,
        "eda_html": None,
        "selected_columns": None,  # For column-specific analysis
        "eda_settings": {},        # For storing EDA preferences

        # Cleaning
        "cleaning_log": [],
        "cleaning_applied": False,
        "missing_values": {},      # Track missing values
        "duplicate_rows": 0,       # Track duplicate count

        # Visualization
        "charts_cache": {},
        "last_viz_config": None,
        "viz_settings": {          # Default visualization settings
            "width": 800,
            "height": 600,
            "theme": "plotly"
        },

        # Analysis
        "analysis_results": {},
        "hypothesis_tests": [],
        "correlation_matrix": None,  # For storing correlation data
        "outliers": {},              # Track outliers in data

        # Modeling
        "models_trained": {},
        "best_model": None,
        "model_metrics": {},
        "feature_importance": None,
        "X_train": None,
        "X_test": None,
        "y_train": None,
        "y_test": None,
        "target_col": None,
        "problem_type": None,
        "hyperparameters": {},       # Store model hyperparameters
        "cv_results": None,          # Cross-validation results

        # MLOps
        "experiments": [],
        "current_experiment": None,
        "registered_models": [],
        "model_registry": {},       # Track registered models

        # Reports
        "last_report_path": None,
        "report_settings": {        # Report generation settings
            "format": "html",
            "include_all": True
        },

        # AI Assistant
        "chat_history": [],
        "ai_provider": "openai",
        "ai_model": "gpt-4o",
        "ai_api_key": "",
        "ai_base_url": "",
        "ai_temperature": 0.7,
        "ai_max_tokens": 8192,       # Increased for more detailed responses
        "ai_system_prompt": (
            "You are a world-class data scientist and analyst. "
            "Help users understand their data, identify patterns, "
            "and provide actionable insights. "
            "Always be specific with recommendations and explain the reasoning behind them. "
            "When suggesting code, use Python with pandas, numpy, and scikit-learn. "
            "Focus on practical, business-relevant insights. "
            "You have access to the full data pipeline including data loading, "
            "preprocessing, EDA, modeling, and deployment stages."
        ),
        "ai_conversation_id": None,  # Track conversation IDs

        # UI State
        "sidebar_collapsed": False,
        "theme": "light",
        "notifications": [],
        "current_page": "Home",
        "ui_settings": {             # UI preferences
            "dark_mode": False,
            "font_size": "normal",
            "auto_save": True
        },
        
        # Dashboards
        "dashboards": {},            # Store dashboard configurations
        
        # Activity logging
        "activity_log": []           # Track user activities and system events
    }

    @classmethod
    def init(cls):
        """Initialize all session state variables with defaults."""
        # Initialize with defaults
        for key, value in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = copy.deepcopy(value)
        
        # Ensure history and future are initialized as lists
        if "history" not in st.session_state:
            st.session_state["history"] = []
        if "future" not in st.session_state:
            st.session_state["future"] = []
        
        # Initialize notifications if not present
        if "notifications" not in st.session_state:
            st.session_state["notifications"] = []
        
        # Initialize activity log if not present
        if "activity_log" not in st.session_state:
            st.session_state["activity_log"] = []
        
        # Initialize dashboards if not present
        if "dashboards" not in st.session_state:
            st.session_state["dashboards"] = {}
    @classmethod
    def save_current_state(cls):
        """Save current data state to history for undo/redo with enhanced tracking."""
        current_df = cls.get("current_df")
        if current_df is not None:
            # Deep copy to prevent reference issues
            state_copy = deepcopy({
                'df': current_df,
                'data_source': cls.get("data_source"),
                'file_name': cls.get("file_name"),
                'cleaning_log': cls.get("cleaning_log"),
                'cleaning_applied': cls.get("cleaning_applied"),
                'missing_values': cls.get("missing_values"),
                'duplicate_rows': cls.get("duplicate_rows"),
                'target_col': cls.get("target_col"),
                'problem_type': cls.get("problem_type"),
                'charts_cache': cls.get("charts_cache"),
                'analysis_results': cls.get("analysis_results")
            })
            
            # Add to history
            history = cls.get("history")
            history.append(state_copy)
            
            # Limit history size based on available memory
            history_limit = cls.get("history_limit")
            if len(history) > history_limit:
                # Remove oldest state
                history.pop(0)
            
            cls.set("history", history)
            # Clear future when new state is added
            cls.set("future", [])
            
            # Log the activity
            cls.add_notification("State saved to history", "info")
    
    @classmethod
    def undo(cls):
        """Undo the last action with enhanced state restoration."""
        history = cls.get("history")
        if len(history) > 0:
            # Move current state to future
            current_state = {
                'df': cls.get("current_df"),
                'data_source': cls.get("data_source"),
                'file_name': cls.get("file_name"),
                'cleaning_log': cls.get("cleaning_log"),
                'cleaning_applied': cls.get("cleaning_applied"),
                'missing_values': cls.get("missing_values"),
                'duplicate_rows': cls.get("duplicate_rows"),
                'target_col': cls.get("target_col"),
                'problem_type': cls.get("problem_type"),
                'charts_cache': cls.get("charts_cache"),
                'analysis_results': cls.get("analysis_results")
            }
            future = cls.get("future")
            future.append(current_state)
            
            # Restore previous state
            prev_state = history.pop()
            cls.set("current_df", prev_state['df'])
            cls.set("data_source", prev_state['data_source'])
            cls.set("file_name", prev_state['file_name'])
            cls.set("cleaning_log", prev_state['cleaning_log'])
            cls.set("cleaning_applied", prev_state['cleaning_applied'])
            cls.set("missing_values", prev_state['missing_values'])
            cls.set("duplicate_rows", prev_state['duplicate_rows'])
            cls.set("target_col", prev_state['target_col'])
            cls.set("problem_type", prev_state['problem_type'])
            cls.set("charts_cache", prev_state['charts_cache'])
            cls.set("analysis_results", prev_state['analysis_results'])
            
            # Update history and future
            cls.set("history", history)
            cls.set("future", future)
            
            # Log the activity
            cls.add_notification("Undo operation completed", "success")
            
            return True
        # Log if undo operation failed
        cls.add_notification("Undo operation failed - no states in history", "warning")
        return False
    
    @classmethod
    def redo(cls):
        """Redo the last undone action with enhanced state restoration."""
        future = cls.get("future")
        if len(future) > 0:
            # Move current state to history
            current_state = {
                'df': cls.get("current_df"),
                'data_source': cls.get("data_source"),
                'file_name': cls.get("file_name"),
                'cleaning_log': cls.get("cleaning_log"),
                'cleaning_applied': cls.get("cleaning_applied"),
                'missing_values': cls.get("missing_values"),
                'duplicate_rows': cls.get("duplicate_rows"),
                'target_col': cls.get("target_col"),
                'problem_type': cls.get("problem_type"),
                'charts_cache': cls.get("charts_cache"),
                'analysis_results': cls.get("analysis_results")
            }
            history = cls.get("history")
            history.append(current_state)
            
            # Restore future state
            future_state = future.pop()
            cls.set("current_df", future_state['df'])
            cls.set("data_source", future_state['data_source'])
            cls.set("file_name", future_state['file_name'])
            cls.set("cleaning_log", future_state['cleaning_log'])
            cls.set("cleaning_applied", future_state['cleaning_applied'])
            cls.set("missing_values", future_state['missing_values'])
            cls.set("duplicate_rows", future_state['duplicate_rows'])
            cls.set("target_col", future_state['target_col'])
            cls.set("problem_type", future_state['problem_type'])
            cls.set("charts_cache", future_state['charts_cache'])
            cls.set("analysis_results", future_state['analysis_results'])
            
            # Update history and future
            cls.set("history", history)
            cls.set("future", future)
            
            # Log the activity
            cls.add_notification("Redo operation completed", "success")
            
            return True
        # Log if redo operation failed
        cls.add_notification("Redo operation failed - no states in future", "warning")
        return False

    @classmethod
    def reset_data(cls):
        """Clear all data-related session state with enhanced cleanup."""
        data_keys = [
            "raw_df", "cleaned_df", "current_df", "data_source", "file_name",
            "eda_report", "eda_html", "cleaning_log", "cleaning_applied",
            "charts_cache", "analysis_results", "models_trained", "best_model",
            "experiments", "current_experiment", "missing_values", 
            "duplicate_rows", "correlation_matrix", "outliers", "cv_results",
            "feature_importance", "X_train", "X_test", "y_train", "y_test"
        ]
        
        # Reset each key to its default value
        for key in data_keys:
            cls.set(key, cls.DEFAULTS.get(key))
        
        # Clear history and future when resetting data
        cls.set("history", [])
        cls.set("future", [])
        
        # Reset AI assistant state
        cls.set("chat_history", [])
        cls.set("ai_conversation_id", None)
        
        # Add notification for data reset
        cls.add_notification("Data has been successfully reset", "success")

    @classmethod
    def get_df(cls) -> Optional[pd.DataFrame]:
        """Get the current active dataframe with enhanced validation."""
        df = cls.get("current_df")
        if df is not None and isinstance(df, pd.DataFrame):
            # Return a deep copy to prevent unintended modifications
            return df.copy()
        return None

    @classmethod
    def set_df(cls, df: pd.DataFrame, source: str = "unknown"):
        """Set the current dataframe and update related state, with history saving."""
        # Save current state to history before changing if there's existing data
        if cls.get("current_df") is not None:
            # Only save if the dataframe actually changed or source changed
            if df is None or not df.equals(cls.get("current_df")) or source != cls.get("data_source"):
                cls.save_current_state()
        
        # Store a copy of the dataframe to prevent reference issues
        cls.set("current_df", df.copy())
        cls.set("data_source", source)
        
        # Reset dependent states
        cls.set("eda_report", None)
        cls.set("cleaning_log", [])
        cls.set("models_trained", {})
        cls.set("analysis_results", {})
        cls.set("charts_cache", {})
        
        # Clear AI analysis state when new data is loaded
        cls.set("chat_history", [])
        cls.set("ai_conversation_id", None)

    @classmethod
    def add_notification(cls, message: str, type_: str = "info", duration: int = 5000, dismissible: bool = True):
        """Add a notification to be displayed with enhanced features."""
        notifications = cls.get("notifications")
        
        # Generate a unique ID for the notification
        notification_id = abs(hash(f"{message}{datetime.now().timestamp()}"))
        
        # Create notification object with additional features
        notification = {
            "message": message,
            "type": type_,
            "id": notification_id,
            "timestamp": datetime.now().timestamp(),
            "read": False,
            "duration": duration,  # Duration in ms
            "dismissible": dismissible,
            "active": True
        }
        
        # Add to notifications list
        notifications.append(notification)
        
        # Keep only the last 15 notifications to prevent memory issues
        cls.set("notifications", notifications[-15:])
        
        # Log the notification as an activity
        cls.log_activity(f"Notification: {message} ({type_})")
    
    @classmethod
    def clear_notifications(cls):
        """Clear all notifications from session state."""
        cls.set("notifications", [])
        cls.log_activity("All notifications cleared")
    
    @classmethod
    def mark_notification_read(cls, notification_id: int):
        """Mark a specific notification as read."""
        notifications = cls.get("notifications")
        for notification in notifications:
            if notification["id"] == notification_id:
                notification["read"] = True
                break
        cls.set("notifications", notifications)
    
    @classmethod
    def get_unread_notifications(cls) -> List[Dict]:
        """Get all unread notifications."""
        notifications = cls.get("notifications")
        return [n for n in notifications if not n["read"]]
    
    @classmethod
    def get_notification_count(cls) -> int:
        """Get total number of notifications."""
        return len(cls.get("notifications"))
    
    @classmethod
    def get_unread_count(cls) -> int:
        """Get number of unread notifications."""
        return len(cls.get_unread_notifications())
    
    @classmethod
    def log_activity(cls, description: str):
        """Log an activity to the activity log with enhanced tracking."""
        timestamp = datetime.now()
        
        # Get user info if available
        user_info = {}
        if "user" in st.session_state:
            user_info = {
                "id": st.session_state.user.get("id"),
                "name": st.session_state.user.get("name"),
                "email": st.session_state.user.get("email")
            }
        
        # Create activity record
        activity = {
            "timestamp": timestamp,
            "description": description,
            "user": user_info,
            "session_id": cls.get("session_id") if "session_id" in st.session_state else None,
            "ip_address": cls.get("ip_address") if "ip_address" in st.session_state else None,
            "user_agent": cls.get("user_agent") if "user_agent" in st.session_state else None,
            "type": "system" if "system" in description.lower() else "user",
            "details": {
                "location": "Data Analysis",
                "action": description.split(" ")[0],
                "timestamp_iso": timestamp.isoformat()
            }
        }
        
        # Add to activity log
        st.session_state.activity_log.append(activity)
        
        # Limit to last 100 activities
        if len(st.session_state.activity_log) > 100:
            st.session_state.activity_log = st.session_state.activity_log[-100:]
    
    @classmethod
    def get_activity_log(cls) -> List[Dict]:
        """Get the activity log with optional filtering."""
        return cls.get("activity_log")
    
    @classmethod
    def filter_activity_log(cls, start_date: datetime = None, end_date: datetime = None, 
                          activity_type: str = None, user_id: str = None) -> List[Dict]:
        """Filter the activity log by various criteria."""
        log = cls.get("activity_log")
        
        if not log:
            return []
        
        # Convert dates to timestamps for comparison
        if start_date:
            start_ts = start_date.timestamp()
            log = [a for a in log if a["timestamp"].timestamp() >= start_ts]
        
        if end_date:
            end_ts = end_date.timestamp()
            log = [a for a in log if a["timestamp"].timestamp() <= end_ts]
        
        if activity_type:
            log = [a for a in log if a["type"] == activity_type]
        
        if user_id:
            log = [a for a in log if a["user"].get("id") == user_id]
        
        return log
    
    @classmethod
    def save_dashboard(cls, dashboard_id: str, dashboard_data: Dict):
        """Save a dashboard configuration with timestamp."""
        dashboards = cls.get("dashboards")
        dashboards[dashboard_id] = {
            "data": dashboard_data,
            "last_modified": datetime.now().timestamp(),
            "created_at": dashboards.get(dashboard_id, {}).get("created_at", datetime.now().timestamp())
        }
        cls.set("dashboards", dashboards)
        cls.log_activity(f"Dashboard saved: {dashboard_id}")
    
    @classmethod
    def delete_dashboard(cls, dashboard_id: str):
        """Delete a dashboard configuration."""
        dashboards = cls.get("dashboards")
        if dashboard_id in dashboards:
            del dashboards[dashboard_id]
            cls.set("dashboards", dashboards)
            cls.log_activity(f"Dashboard deleted: {dashboard_id}")
    
    @classmethod
    def get_all_dashboards(cls) -> Dict[str, Dict]:
        """Get all dashboard configurations with metadata."""
        return cls.get("dashboards")
    
    @classmethod
    def get_dashboard(cls, dashboard_id: str) -> Optional[Dict]:
        """Get a specific dashboard configuration."""
        dashboards = cls.get("dashboards")
        return dashboards.get(dashboard_id)
    
    @classmethod
    def clear_dashboards(cls):
        """Clear all dashboard configurations."""
        cls.set("dashboards", {})
        cls.log_activity("All dashboards cleared")
    @classmethod
    def add_notification(cls, message: str, type_: str = "info"):
        """Add a notification to be displayed."""
        notifications = cls.get("notifications")
        notifications.append({"message": message, "type": type_, "id": pd.Timestamp.now().timestamp()})
        cls.set("notifications", notifications[-5:])  # Keep last 5
    @classmethod
    def add_notification(cls, message: str, type_: str = "info"):
        """Add a notification to be displayed."""
        notifications = cls.get("notifications")
        notifications.append({"message": message, "type": type_, "id": pd.Timestamp.now().timestamp()})
        cls.set("notifications", notifications[-5:])  # Keep last 5
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a session state value."""
        cls.init()
        return st.session_state.get(key, cls.DEFAULTS.get(key, default))

    @classmethod
    def set(cls, key: str, value: Any):
        """Set a session state value."""
        cls.init()
        st.session_state[key] = value

    @classmethod
    def append(cls, key: str, value: Any):
        """Append to a list session state value."""
        cls.init()
        if key not in st.session_state or st.session_state[key] is None:
            st.session_state[key] = []
        st.session_state[key].append(value)

    @classmethod
    def has_data(cls) -> bool:
        """Check if any dataframe is loaded."""
        df = cls.get("current_df")
        return df is not None and isinstance(df, pd.DataFrame) and not df.empty

    @classmethod
    def get_df(cls) -> Optional[pd.DataFrame]:
        """Get the current active dataframe."""
        df = cls.get("current_df")
        if df is not None and isinstance(df, pd.DataFrame):
            return df.copy()
        return None

    @classmethod
    def set_df(cls, df: pd.DataFrame, source: str = "unknown"):
        """Set the current dataframe and update related state, with history saving."""
        # Save current state to history before changing if there's existing data
        if cls.get("current_df") is not None:
            # Only save if the dataframe actually changed or source changed
            if df is None or not df.equals(cls.get("current_df")) or source != cls.get("data_source"):
                cls.save_current_state()
        
        cls.set("current_df", df.copy())
        cls.set("data_source", source)
        # Reset dependent states
        cls.set("eda_report", None)
        cls.set("cleaning_log", [])
        cls.set("models_trained", {})
        cls.set("analysis_results", {})
        cls.set("charts_cache", {})

    @classmethod
    def reset_data(cls):
        """Clear all data-related session state."""
        data_keys = ["raw_df", "cleaned_df", "current_df", "data_source", "file_name",
                     "eda_report", "eda_html", "cleaning_log", "cleaning_applied",
                     "charts_cache", "analysis_results", "models_trained", "best_model",
                     "experiments", "current_experiment"]
        for key in data_keys:
            cls.set(key, cls.DEFAULTS.get(key))
        
        # Clear history and future when resetting data
        cls.set("history", [])
        cls.set("future", [])

    @classmethod
    def add_notification(cls, message: str, type_: str = "info"):
        """Add a notification to be displayed."""
        notifications = cls.get("notifications")
        notifications.append({"message": message, "type": type_, "id": pd.Timestamp.now().timestamp()})
        cls.set("notifications", notifications[-5:])  # Keep last 5

    @classmethod
    def clear_notifications(cls):
        """Clear all notifications."""
        cls.set("notifications", [])

    @classmethod
    def save_current_state(cls):
        """Save current data state to history for undo/redo."""
        current_df = cls.get("current_df")
        if current_df is not None:
            # Deep copy to prevent reference issues
            state_copy = copy.deepcopy({
                'df': current_df,
                'data_source': cls.get("data_source"),
                'file_name': cls.get("file_name"),
                # Add other important state variables here
                'cleaning_log': cls.get("cleaning_log"),
                'cleaning_applied': cls.get("cleaning_applied")
            })
            
            # Add to history
            history = cls.get("history")
            history.append(state_copy)
            
            # Limit history size
            history_limit = cls.get("history_limit")
            if len(history) > history_limit:
                history = history[-history_limit:]
            
            cls.set("history", history)
            # Clear future when new state is added
            cls.set("future", [])

    @classmethod
    def undo(cls):
        """Undo the last action."""
        history = cls.get("history")
        if len(history) > 0:
            # Move current state to future
            current_state = {
                'df': cls.get("current_df"),
                'data_source': cls.get("data_source"),
                'file_name': cls.get("file_name"),
                'cleaning_log': cls.get("cleaning_log"),
                'cleaning_applied': cls.get("cleaning_applied")
            }
            future = cls.get("future")
            future.append(current_state)
            
            # Restore previous state
            prev_state = history.pop()
            cls.set("current_df", prev_state['df'])
            cls.set("data_source", prev_state['data_source'])
            cls.set("file_name", prev_state['file_name'])
            cls.set("cleaning_log", prev_state['cleaning_log'])
            cls.set("cleaning_applied", prev_state['cleaning_applied'])
            
            # Update history and future
            cls.set("history", history)
            cls.set("future", future)
            
            return True
        return False

    @classmethod
    def redo(cls):
        """Redo the last undone action."""
        future = cls.get("future")
        if len(future) > 0:
            # Move current state to history
            current_state = {
                'df': cls.get("current_df"),
                'data_source': cls.get("data_source"),
                'file_name': cls.get("file_name"),
                'cleaning_log': cls.get("cleaning_log"),
                'cleaning_applied': cls.get("cleaning_applied")
            }
            history = cls.get("history")
            history.append(current_state)
            
            # Restore future state
            future_state = future.pop()
            cls.set("current_df", future_state['df'])
            cls.set("data_source", future_state['data_source'])
            cls.set("file_name", future_state['file_name'])
            cls.set("cleaning_log", future_state['cleaning_log'])
            cls.set("cleaning_applied", future_state['cleaning_applied'])
            
            # Update history and future
            cls.set("history", history)
            cls.set("future", future)
            
            return True
        return False

    @classmethod
    def get_history_length(cls):
        """Get the number of states in history."""
        return len(cls.get("history"))

    @classmethod
    def get_future_length(cls):
        """Get the number of states in future."""
        return len(cls.get("future"))

    @classmethod
    def get_activity_log(cls):
        """Get the activity log from notifications or chat history."""
        # Check if we have notifications with activity info
        notifications = cls.get("notifications", [])
        
        # Extract activity messages from notifications
        activities = []
        for notification in notifications:
            if isinstance(notification, dict) and "message" in notification:
                activities.append(f"[Notification] {notification['message']}")
        
        # Also include recent chat messages if available
        chat_history = cls.get("chat_history", [])
        for chat in reversed(chat_history[-3:]):  # Last 3 chat messages
            if isinstance(chat, dict) and "content" in chat:
                activities.append(f"[Chat] {chat['content'][:100]}...")  # Truncate long messages
        
        # If no activities found, return a default message
        if not activities:
            activities = ["Started application", "No recent activity"]
        
        # Return the last few activities (reverse to show newest first)
        return activities[-10:]  # Return last 10 activities

# No changes needed to the init_session function as it's being replaced by the SessionManager.init() method
