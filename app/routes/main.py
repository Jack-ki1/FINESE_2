"""
FINESE2 - Main Dashboard Routes
Serves the main dashboard interface and basic routes.
"""
from flask import Blueprint, render_template, jsonify, send_from_directory
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Serve the main dashboard page.
    
    Returns:
        Rendered HTML template
    """
    # dashboard/templates contains dashboard.html (not index.html)
    return render_template('dashboard.html')


@main_bp.route('/dashboard')
def dashboard():
    """
    Serve the dashboard page (alias for index).
    
    Returns:
        Rendered HTML template
    """
    return render_template('dashboard.html')


@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """
    Serve uploaded files securely.
    
    Args:
        filename: Name of the file to serve
        
    Returns:
        File response or 404
    """
    upload_folder = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'dashboard',
        'uploads'
    )
    
    # Security: Ensure file exists and is within upload folder
    safe_path = os.path.join(upload_folder, filename)
    if not os.path.exists(safe_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_from_directory(upload_folder, filename)


@main_bp.route('/about')
def about():
    """
    Serve the about page with platform information.
    
    Returns:
        JSON with platform info
    """
    return jsonify({
        'name': 'FINESE2',
        'version': '3.0.0',
        'description': 'Professional Data Intelligence Platform',
        'features': [
            'Data Upload & Management',
            'Automated EDA & Profiling',
            'Interactive Visualizations',
            'Machine Learning AutoML',
            'AI-Powered Assistant',
            'MLOps Experiment Tracking'
        ]
    })


@main_bp.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors for undefined routes."""
    return jsonify({'error': 'Page not found'}), 404
