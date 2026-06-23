"""
FINESE2 - Report Generation API Routes
Handles report creation and export.
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import io
from app.services.data_service import data_service
from app.services.report_service import report_service

logger = logging.getLogger(__name__)

reports_bp = Blueprint('api_reports', __name__)


@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_report():
    """Generate a report."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        report_type = request.json.get('report_type', 'html')
        params = request.json.get('params', {})
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        result = report_service.generate_report(
            df=df,
            report_type=report_type,
            params=params,
            user_id=user_id,
            dataset_id=dataset_id
        )
        
        # For HTML and markdown, return content directly
        if report_type in ['html', 'markdown']:
            return jsonify({
                'content': result['content'],
                'format': result['format'],
                'title': result['title']
            }), 200
        
        # For Excel, return as file download
        elif report_type == 'excel':
            return send_file(
                io.BytesIO(result['content']),
                mimetype=result['format'],
                as_attachment=True,
                download_name=f"{result['title'].replace(' ', '_')}.xlsx"
            )
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/types', methods=['GET'])
@jwt_required()
def get_report_types():
    """Get available report types."""
    report_types = [
        {'type': 'html', 'name': 'HTML Report', 'description': 'Interactive web report'},
        {'type': 'excel', 'name': 'Excel Report', 'description': 'Multi-sheet Excel workbook'},
        {'type': 'markdown', 'name': 'Markdown Report', 'description': 'Text-based report'}
    ]
    
    return jsonify({'report_types': report_types}), 200
