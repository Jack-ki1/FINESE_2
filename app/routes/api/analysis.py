"""
FINESE2 - Statistical Analysis API Routes
Handles hypothesis testing and statistical analysis.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.services.data_service import data_service
from app.services.analysis_service import analysis_service

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('api_analysis', __name__)


@analysis_bp.route('/perform', methods=['POST'])
@jwt_required()
def perform_analysis():
    """Perform statistical analysis."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        analysis_type = request.json.get('analysis_type')
        params = request.json.get('params', {})
        
        if not dataset_id or not analysis_type:
            return jsonify({'error': 'Dataset ID and analysis type required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        result = analysis_service.perform_analysis(
            df=df,
            analysis_type=analysis_type,
            params=params,
            user_id=user_id,
            dataset_id=dataset_id
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """Get analysis templates."""
    templates = analysis_service.get_analysis_templates()
    return jsonify({'templates': templates}), 200
