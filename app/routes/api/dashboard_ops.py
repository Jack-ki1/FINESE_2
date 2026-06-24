"""
FINESE2 - Dashboard Operations API Routes
Handles dashboard operations, reports, and dashboard-related functionality.
"""
from flask import Blueprint, request, jsonify
import logging
from app.core.dashboard import dashboard_manager
from app.core.reports import report_generator
from app.core.visualize import visualizer
from app.core.data import data_manager

logger = logging.getLogger(__name__)

dashboard_ops_bp = Blueprint('api_dashboard_ops', __name__)


@dashboard_ops_bp.route('/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Get dashboard overview data."""
    try:
        dashboard_data = dashboard_manager.get_dashboard_data()
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Getting dashboard data failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_ops_bp.route('/create-report', methods=['POST'])
def create_report():
    """Create a new report."""
    try:
        report_type = request.json.get('type', 'summary')
        dataset_id = request.json.get('dataset_id')
        title = request.json.get('title', 'Auto-generated Report')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Generate report based on type
        report = report_generator.generate_report(df, report_type, title)
        
        return jsonify({
            'report_id': report['id'],
            'report_url': report['url'],
            'title': report['title'],
            'generated_at': report['generated_at']
        }), 200
        
    except Exception as e:
        logger.error(f"Report creation failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_ops_bp.route('/export-report', methods=['POST'])
def export_report():
    """Export a report in specified format."""
    try:
        report_id = request.json.get('report_id')
        export_format = request.json.get('format', 'html')
        
        if not report_id:
            return jsonify({'error': 'Report ID required'}), 400
        
        exported_report = report_generator.export_report(report_id, export_format)
        
        return jsonify({
            'success': True,
            'download_url': exported_report['download_url'],
            'format': export_format,
            'size': exported_report['size']
        }), 200
        
    except Exception as e:
        logger.error(f"Report export failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_ops_bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    """Get recent user activity."""
    try:
        activity = dashboard_manager.get_recent_activity()
        
        return jsonify(activity), 200
        
    except Exception as e:
        logger.error(f"Getting recent activity failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_ops_bp.route('/model-performance', methods=['GET'])
def get_model_performance():
    """Get model performance metrics for dashboard."""
    try:
        performance_metrics = dashboard_manager.get_model_performance_metrics()
        
        return jsonify(performance_metrics), 200
        
    except Exception as e:
        logger.error(f"Getting model performance metrics failed: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_ops_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    """Generate a report for a dataset."""
    try:
        from app.core.reports import report_generator
        
        dataset_id = request.json.get('dataset_id')
        report_type = request.json.get('report_type', 'basic')
        title = request.json.get('title', 'FINESE2 Report')
        format_type = request.json.get('format', 'json')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Generate report
        report = report_generator.generate_report(df, report_type, title)
        
        return jsonify({
            'success': True,
            'title': title,
            'report_type': report_type,
            'format': format_type,
            'report_data': report
        }), 200
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({'error': str(e)}), 500
