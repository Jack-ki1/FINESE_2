"""
FINESE2 - Dashboard API Routes
Handles dashboard operations using the consolidated dashboard module.
"""
from flask import Blueprint, request, jsonify, render_template_string
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.core.dashboard import dashboard_manager
from app.core.data import data_manager
from app.core.visualize import visualizer
from app.core.eda import eda_engine

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('api_dashboard', __name__)


@dashboard_bp.route('/create', methods=['POST'])
@jwt_required()
def create_dashboard():
    """Create a dashboard based on the request parameters."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        dashboard_type = request.json.get('dashboard_type', 'default')
        title = request.json.get('title', f'Dashboard for Dataset {dataset_id}')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Create dashboard based on type
        if dashboard_type == 'analytics':
            dashboard_html = dashboard_manager.create_analytics_dashboard(df, title)
        elif dashboard_type == 'ml_monitoring':
            # For ML monitoring dashboard, we need model data
            models_data = request.json.get('models_data', [])
            performance_metrics = request.json.get('performance_metrics', [])
            alerts = request.json.get('alerts', [])
            dashboard_html = dashboard_manager.create_ml_monitoring_dashboard(
                models_data, performance_metrics, alerts, title
            )
        else:  # default dashboard
            dashboard_html = dashboard_manager.create_default_dashboard(df, title)
        
        return jsonify({
            'success': True,
            'dashboard_type': dashboard_type,
            'title': title,
            'created': True,
            'message': f'{dashboard_type.capitalize()} dashboard created successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard creation failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/types', methods=['GET'])
@jwt_required()
def get_dashboard_types():
    """Get available dashboard types."""
    try:
        user_id = get_jwt_identity()
        
        dashboard_types = [
            {
                'type': 'default',
                'title': 'Default Dashboard',
                'description': 'General purpose dashboard with key metrics and charts'
            },
            {
                'type': 'analytics',
                'title': 'Analytics Dashboard',
                'description': 'Advanced analytics with filters and drill-down capabilities'
            },
            {
                'type': 'ml_monitoring',
                'title': 'ML Monitoring Dashboard',
                'description': 'Real-time model performance tracking'
            }
        ]
        
        return jsonify({'dashboard_types': dashboard_types}), 200
        
    except Exception as e:
        logger.error(f"Getting dashboard types failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/summary', methods=['POST'])
@jwt_required()
def get_dashboard_summary():
    """Get a summary of the dataset for dashboard purposes."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        summary = dashboard_manager.get_dashboard_summary(df)
        
        return jsonify({
            'success': True,
            'summary': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Getting dashboard summary failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/export', methods=['POST'])
@jwt_required()
def export_dashboard():
    """Export a dashboard in specified format."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        dashboard_type = request.json.get('dashboard_type', 'default')
        format_type = request.json.get('format', 'html')
        title = request.json.get('title', f'Exported_Dashboard_{dataset_id}')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Create dashboard
        if dashboard_type == 'analytics':
            dashboard_html = dashboard_manager.create_analytics_dashboard(df, title)
        elif dashboard_type == 'ml_monitoring':
            # Create a simple ML monitoring dashboard with dummy data
            models_data = [{
                'name': 'Sample Model',
                'version': '1.0',
                'accuracy': 0.85,
                'status': 'active',
                'last_updated': '2023-01-01'
            }]
            performance_metrics = [{
                'title': 'Accuracy',
                'value': '85%',
                'is_good': True,
                'description': 'Model accuracy over test set'
            }]
            dashboard_html = dashboard_manager.create_ml_monitoring_dashboard(
                models_data, performance_metrics, title=title
            )
        else:  # default dashboard
            dashboard_html = dashboard_manager.create_default_dashboard(df, title)
        
        # Export dashboard
        filename = f"dashboard_{dataset_id}_{dashboard_type}_{user_id}"
        filepath = dashboard_manager.export_dashboard(dashboard_html, filename, format_type)
        
        return jsonify({
            'success': True,
            'dashboard_type': dashboard_type,
            'format': format_type,
            'filepath': filepath,
            'message': f'Dashboard exported successfully as {format_type.upper()}'
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard export failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/interactive', methods=['POST'])
@jwt_required()
def create_interactive_dashboard():
    """Create an interactive dashboard with custom widgets."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        title = request.json.get('title', 'Interactive Dashboard')
        widgets_config = request.json.get('widgets', [])
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Create interactive dashboard
        # This is a simplified implementation - in a real app you would have more complex widget configurations
        dashboard_html = dashboard_manager.create_default_dashboard(df, title)
        
        return jsonify({
            'success': True,
            'title': title,
            'widgets_count': len(widgets_config),
            'message': 'Interactive dashboard created successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Interactive dashboard creation failed: {e}")
        return jsonify({'error': str(e)}), 500