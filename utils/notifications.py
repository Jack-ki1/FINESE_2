"""
Notification Center for FINESE2
Manages system notifications, warnings, and user alerts
"""
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import json


class NotificationCenter:
    """Manages notifications across the application."""
    
    @staticmethod
    def add_notification(level: str, message: str, duration: int = 5):
        """
        Add a notification to the session state.
        
        Args:
            level: 'info', 'success', 'warning', or 'error'
            message: The notification message
            duration: How long to show the notification (in seconds)
        """
        notification = {
            'id': len(st.session_state.notifications) if 'notifications' in st.session_state else 0,
            'level': level,
            'message': message,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'duration': duration
        }
        
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        st.session_state.notifications.append(notification)
        
        # Show the notification
        if level == 'error':
            st.error(message)
        elif level == 'warning':
            st.warning(message)
        elif level == 'success':
            st.success(message)
        else:
            st.info(message)
    
    @staticmethod
    def get_recent_notifications(limit: int = 10) -> List[Dict]:
        """Get the most recent notifications."""
        if 'notifications' not in st.session_state:
            return []
        return st.session_state.notifications[-limit:]
    
    @staticmethod
    def clear_notifications():
        """Clear all notifications."""
        st.session_state.notifications = []
    
    @staticmethod
    def show_notification_panel():
        """Display the notification panel in the sidebar."""
        with st.sidebar.expander("🔔 Notifications", expanded=True):
            notifications = NotificationCenter.get_recent_notifications()
            
            if not notifications:
                st.write("No recent notifications")
                return
            
            # Sort by newest first
            notifications.reverse()
            
            for note in notifications[:5]:  # Show only last 5
                icon = "ℹ️" if note['level'] == 'info' else \
                       "✅" if note['level'] == 'success' else \
                       "⚠️" if note['level'] == 'warning' else "❌"
                
                st.markdown(f"<div class='notification'>{icon} {note['message']}</div>", 
                           unsafe_allow_html=True)
            
            if len(notifications) > 5:
                st.caption(f"+ {len(notifications) - 5} more notifications")
            
            if st.button("Clear All", key="clear_notifications", use_container_width=True):
                NotificationCenter.clear_notifications()
                st.rerun()
    
    @staticmethod
    def show_system_alerts():
        """Show system-level alerts in the main content area."""
        if 'system_alerts' not in st.session_state:
            st.session_state.system_alerts = []
        
        for alert in st.session_state.system_alerts:
            if alert['level'] == 'error':
                st.error(alert['message'])
            elif alert['level'] == 'warning':
                st.warning(alert['message'])
            elif alert['level'] == 'info':
                st.info(alert['message'])
            elif alert['level'] == 'success':
                st.success(alert['message'])


def render_notification_center():
    """Render the notification center component."""
    NotificationCenter.show_notification_panel()


def add_notification(level: str, message: str, duration: int = 5):
    """Helper function to add a notification."""
    NotificationCenter.add_notification(level, message, duration)