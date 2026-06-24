"""
FINESE2 - Route Registration
Centralized blueprint registration for all API routes.
"""
from flask import Flask


def register_blueprints(app: Flask) -> None:
    """
    Register all blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Consolidated API routes
    from app.routes.api.data_ops import data_ops_bp
    from app.routes.api.ml_ops import ml_ops_bp
    from app.routes.api.dashboard_ops import dashboard_ops_bp
    from app.routes.api.eda_ops import eda_ops_bp  # Added EDA operations

    # Optional modules introduced in A–G implementation
    try:
        from app.routes.api.jobs_ops import jobs_ops_bp  # type: ignore
    except Exception:
        jobs_ops_bp = None

    try:
        from app.routes.api.ai_ops import ai_ops_bp  # type: ignore
    except Exception:
        ai_ops_bp = None
    
    # Register API routes under /api/v1 prefix
    app.register_blueprint(data_ops_bp, url_prefix='/api/v1/data')
    app.register_blueprint(ml_ops_bp, url_prefix='/api/v1/ml')
    app.register_blueprint(dashboard_ops_bp, url_prefix='/api/v1/dashboard')
    app.register_blueprint(eda_ops_bp, url_prefix='/api/v1/eda')  # Added EDA endpoint
    
    # Also register ml_ops under /api/v1/mlops for frontend compatibility
    try:
        from app.routes.api.ml_ops import ml_ops_bp as mlops_bp
        app.register_blueprint(mlops_bp, url_prefix='/api/v1/mlops')
    except Exception:
        pass
    
    # Also register dashboard_ops under /api/v1/reports for frontend compatibility
    try:
        from app.routes.api.dashboard_ops import dashboard_ops_bp as reports_bp
        app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    except Exception:
        pass

    # A–G: async jobs + AI tool execution
    if jobs_ops_bp is not None:
        app.register_blueprint(jobs_ops_bp, url_prefix='/api/v1/jobs')

    if ai_ops_bp is not None:
        app.register_blueprint(ai_ops_bp, url_prefix='/api/v1/ai')

    # Tokenized tool execution alias expected by some docs/clients
    # (keep backwards compatible)
    if ai_ops_bp is not None:
        try:
            app.register_blueprint(ai_ops_bp, url_prefix='/api/v1/tools')
        except Exception:
            pass

    # Main routes (no prefix)
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
