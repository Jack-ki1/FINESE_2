"""
Utility functions for the FINESE2 application.
"""
import os
from functools import wraps
from flask import request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError


def conditional_jwt_required(func):
    """
    A decorator that makes JWT required in production but optional in development.
    In development, if no token is provided, user_id will be set to 'dev_user' by default.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if we're in development mode
        is_development = current_app.config.get('ENVIRONMENT', 'development') == 'development' or \
                        current_app.config.get('DEBUG', False)
        
        user_identity = None
        token_present = False
        
        try:
            # Try to verify JWT token if present
            verify_jwt_in_request()
            user_identity = get_jwt_identity()
            token_present = True
        except NoAuthorizationError:
            # No token provided
            if is_development:
                # In development, assign a default user identity
                user_identity = 'dev_user'
            else:
                # In production, raise the authorization error
                raise
        
        # Add user identity to request context for use in route functions
        request.current_user_id = user_identity
        
        return func(*args, **kwargs)
    
    return wrapper