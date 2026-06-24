"""
FINESE2 - Main Routes
Handles main application pages and entry points.
"""
from flask import Blueprint, render_template, current_app, send_from_directory, jsonify, request
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Main dashboard page - serves the comprehensive dashboard.html."""
    return render_template('dashboard.html')


@main_bp.route('/dashboard')
def dashboard():
    """Dashboard page - same as index for consistency."""
    return render_template('dashboard.html')


@main_bp.route('/analytics')
def analytics():
    """Analytics dashboard view."""
    return render_template('dashboard.html')


@main_bp.route('/ml-monitoring')
def ml_monitoring():
    """ML monitoring dashboard view."""
    return render_template('dashboard.html')


@main_bp.route('/api-docs')
def api_docs():
    """API documentation page."""
    # For now, redirect to a simple API info endpoint
    return jsonify({
        'api_version': 'v1',
        'documentation': 'See README.md for API documentation',
        'endpoints': {
            'data': '/api/v1/data/*',
            'ml': '/api/v1/ml/*',
            'dashboard': '/api/v1/dashboard/*',
            'jobs': '/api/v1/jobs/*',
            'ai': '/api/v1/ai/*'
        }
    })


@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    try:
        return send_from_directory(
            os.path.join(current_app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    except Exception:
        # Return empty response if favicon doesn't exist
        return '', 204


@main_bp.app_errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    # For SPA (Single Page Application), return dashboard.html for all non-API routes
    if not request.path.startswith('/api/'):
        return render_template('dashboard.html'), 404
    
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found',
        'path': request.path
    }), 404


@main_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An internal server error occurred'
    }), 500
