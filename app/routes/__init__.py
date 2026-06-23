"""
FINESE2 - Route Blueprint Registration
Centralized registration of all route blueprints.
"""


def register_blueprints(app):
    """
    Register all Flask blueprints with the application.
    
    Args:
        app: Flask application instance
    """
    # Import blueprints here to avoid circular imports
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    
    # Register authentication blueprint
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Register main blueprint (dashboard routes)
    app.register_blueprint(main_bp)
    
    # Register API blueprints
    from app.routes.api import register_api_blueprints
    register_api_blueprints(app)
