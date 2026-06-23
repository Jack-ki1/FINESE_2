"""
FINESE2 - API Routes Registration
Registers all API blueprints for the application.
"""


def register_api_blueprints(app):
    """
    Register all API blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    from app.routes.api.data import data_bp
    from app.routes.api.eda import eda_bp
    from app.routes.api.cleaning import cleaning_bp
    from app.routes.api.visualization import visualization_bp
    from app.routes.api.analysis import analysis_bp
    from app.routes.api.ml import ml_bp
    from app.routes.api.mlops import mlops_bp
    from app.routes.api.reports import reports_bp
    from app.routes.api.ai import ai_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(data_bp, url_prefix='/api/data')
    app.register_blueprint(eda_bp, url_prefix='/api/eda')
    app.register_blueprint(cleaning_bp, url_prefix='/api/cleaning')
    app.register_blueprint(visualization_bp, url_prefix='/api/visualization')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(mlops_bp, url_prefix='/api/mlops')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
