"""
FINESE2 - Helper Utilities
Common helper functions used throughout the application.
"""
import os
from functools import wraps
from flask import current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError


def jwt_optional_dev(f):
    """
    Decorator that makes JWT optional in development mode but required in production.
    In development, if no JWT is present, it returns a default user ID (e.g., 1).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if we're in development mode
        is_development = os.environ.get('FLASK_ENV', 'development') == 'development'
        
        try:
            # Try to verify JWT normally
            verify_jwt_in_request()
            # If successful, get the identity and proceed normally
            return f(*args, **kwargs)
        except NoAuthorizationError:
            # If no authorization header is present
            if is_development:
                # In development mode, allow the request to proceed with a default user
                # We'll mock the user identity by setting it in the request context
                from flask import g
                g.default_user_id = 1  # Default user ID for development
                return f(*args, **kwargs)
            else:
                # In production, raise the exception
                raise
    
    return decorated_function


def get_current_user_id():
    """
    Get current user ID, handling both production (with JWT) and development (with optional JWT) modes.
    """
    try:
        # Try to get user ID from JWT
        user_id = get_jwt_identity()
        return user_id
    except NoAuthorizationError:
        # If JWT is not available, check if we're in development and use default
        from flask import current_app, g
        is_development = current_app.config.get('ENVIRONMENT', 'development') == 'development'
        if is_development and hasattr(g, 'default_user_id'):
            return g.default_user_id
        else:
            raise NoAuthorizationError("Authorization header is expected")


def is_development_mode():
    """
    Check if the application is running in development mode.
    """
    return os.environ.get('FLASK_ENV', 'development') == 'development'