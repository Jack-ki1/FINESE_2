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
    # Core API routes
    from app.routes.api.data import data_bp
    from app.routes.api.eda import eda_bp
    from app.routes.api.cleaning import cleaning_bp
    from app.routes.api.visualization import visualization_bp
    from app.routes.api.analysis import analysis_bp
    from app.routes.api.ml import ml_bp
    from app.routes.api.mlops import mlops_bp
    from app.routes.api.reports import reports_bp
    from app.routes.api.dashboard import dashboard_bp
    
    # Register API routes under /api/v1 prefix
    app.register_blueprint(data_bp, url_prefix='/api/v1/data')
    app.register_blueprint(eda_bp, url_prefix='/api/v1/eda')
    app.register_blueprint(cleaning_bp, url_prefix='/api/v1/cleaning')
    app.register_blueprint(visualization_bp, url_prefix='/api/v1/visualization')
    app.register_blueprint(analysis_bp, url_prefix='/api/v1/analysis')
    app.register_blueprint(ml_bp, url_prefix='/api/v1/ml')
    app.register_blueprint(mlops_bp, url_prefix='/api/v1/mlops')
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')

    # Main routes (no prefix)
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)