"""
FINESE2 - Reports API Routes
Handles report generation operations using the consolidated reports module.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.core.reports import report_generator
from app.core.data import data_manager
from app.core.eda import eda_engine
from app.core.analysis import analysis_engine
from app.core.ml_models import ml_model_manager

logger = logging.getLogger(__name__)

reports_bp = Blueprint('api_reports', __name__)


@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_report():
    """Generate a report based on the request parameters."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        report_type = request.json.get('report_type', 'basic')
        title = request.json.get('title', 'Data Report')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Generate report based on type
        if report_type == 'basic':
            report_html = report_generator.generate_basic_report(df, title)
        elif report_type == 'eda':
            report_html = report_generator.generate_eda_report(df, title)
        elif report_type == 'comprehensive':
            report_html = report_generator.generate_comprehensive_report(df, ['basic', 'eda'], title)
        else:
            return jsonify({'error': f'Report type {report_type} not supported'}), 400
        
        # For now, return a success message since we can't easily return HTML through API
        return jsonify({
            'success': True,
            'report_type': report_type,
            'title': title,
            'generated': True,
            'message': f'{report_type.capitalize()} report generated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/types', methods=['GET'])
@jwt_required()
def get_report_types():
    """Get available report types."""
    try:
        user_id = get_jwt_identity()
        
        report_types = [
            {
                'type': 'basic',
                'title': 'Basic Report',
                'description': 'Simple overview of dataset characteristics'
            },
            {
                'type': 'eda',
                'title': 'EDA Report',
                'description': 'Comprehensive exploratory data analysis'
            },
            {
                'type': 'comprehensive',
                'title': 'Comprehensive Report',
                'description': 'Full dataset analysis with multiple sections'
            },
            {
                'type': 'ml',
                'title': 'ML Report',
                'description': 'Machine learning model performance report'
            },
            {
                'type': 'comparison',
                'title': 'Model Comparison Report',
                'description': 'Comparison of multiple models'
            }
        ]
        
        return jsonify({'report_types': report_types}), 200
        
    except Exception as e:
        logger.error(f"Getting report types failed: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/eda', methods=['POST'])
@jwt_required()
def generate_eda_report():
    """Generate an EDA report."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        title = request.json.get('title', 'EDA Report')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        report_html = report_generator.generate_eda_report(df, title)
        
        return jsonify({
            'success': True,
            'report_type': 'eda',
            'title': title,
            'generated': True
        }), 200
        
    except Exception as e:
        logger.error(f"EDA report generation failed: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/summary-stats', methods=['POST'])
@jwt_required()
def get_summary_statistics():
    """Get summary statistics for a dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        summary = report_generator.generate_summary_statistics(df)
        
        return jsonify({
            'success': True,
            'summary': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Summary statistics generation failed: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/export', methods=['POST'])
@jwt_required()
def export_report():
    """Export a report in specified format."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        report_type = request.json.get('report_type', 'basic')
        format_type = request.json.get('format', 'html')
        title = request.json.get('title', 'Exported_Report')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Generate report
        if report_type == 'basic':
            report_html = report_generator.generate_basic_report(df, title)
        elif report_type == 'eda':
            report_html = report_generator.generate_eda_report(df, title)
        elif report_type == 'comprehensive':
            report_html = report_generator.generate_comprehensive_report(df, ['basic', 'eda'], title)
        else:
            return jsonify({'error': f'Report type {report_type} not supported'}), 400
        
        # Export report
        filename = f"report_{dataset_id}_{report_type}_{user_id}"
        filepath = report_generator.export_report(report_html, filename, format_type)
        
        return jsonify({
            'success': True,
            'report_type': report_type,
            'format': format_type,
            'filepath': filepath,
            'message': f'Report exported successfully as {format_type.upper()}'
        }), 200
        
    except Exception as e:
        logger.error(f"Report export failed: {e}")
        return jsonify({'error': str(e)}), 500