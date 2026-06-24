"""
API Routes Package
Defines all API routes for the FINESE2 platform.
"""
from flask import Blueprint


# Create the main API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


# Import and register individual API route blueprints
def register_api_routes(api_bp):
    """
    Register all API routes with the main API blueprint.
    
    Args:
        api_bp: The main API blueprint
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
    
    # Register blueprints
    api_bp.register_blueprint(data_bp, url_prefix='/data')
    api_bp.register_blueprint(eda_bp, url_prefix='/eda')
    api_bp.register_blueprint(cleaning_bp, url_prefix='/cleaning')
    api_bp.register_blueprint(visualization_bp, url_prefix='/visualization')
    api_bp.register_blueprint(analysis_bp, url_prefix='/analysis')
    api_bp.register_blueprint(ml_bp, url_prefix='/ml')
    api_bp.register_blueprint(mlops_bp, url_prefix='/mlops')
    api_bp.register_blueprint(reports_bp, url_prefix='/reports')
    api_bp.register_blueprint(dashboard_bp, url_prefix='/dashboard')


# Register routes when module is imported
register_api_routes(api_bp)

# Import all API route blueprints to make them easily accessible
from .data import data_bp
from .eda import eda_bp
from .cleaning import cleaning_bp
from .visualization import visualization_bp
from .analysis import analysis_bp
from .ml import ml_bp
from .mlops import mlops_bp
from .reports import reports_bp
from .dashboard import dashboard_bp


# Define what gets imported with "from app.routes.api import *"
__all__ = [
    'data_bp',
    'eda_bp',
    'cleaning_bp',
    'visualization_bp',
    'analysis_bp',
    'ml_bp',
    'mlops_bp',
    'reports_bp',
    'dashboard_bp',
    'ai_bp'
]