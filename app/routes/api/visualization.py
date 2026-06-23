"""
FINESE2 - Visualization API Routes
Handles chart creation and management.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.services.data_service import data_service
from app.services.visualization_service import visualization_service

logger = logging.getLogger(__name__)

visualization_bp = Blueprint('api_visualization', __name__)


@visualization_bp.route('/create', methods=['POST'])
@jwt_required()
def create_chart():
    """Create a visualization chart."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        chart_type = request.json.get('chart_type')
        params = request.json.get('params', {})
        
        if not dataset_id or not chart_type:
            return jsonify({'error': 'Dataset ID and chart type required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        cache_key = f"user_{user_id}_dataset_{dataset_id}_{chart_type}"
        
        result = visualization_service.create_chart(
            df=df,
            chart_type=chart_type,
            params=params,
            user_id=user_id,
            cache_key=cache_key
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Chart creation failed: {e}")
        return jsonify({'error': str(e)}), 500


@visualization_bp.route('/types', methods=['GET'])
@jwt_required()
def get_chart_types():
    """Get available chart types."""
    chart_types = [
        {'type': 'bar', 'name': 'Bar Chart', 'description': 'Compare categories'},
        {'type': 'line', 'name': 'Line Chart', 'description': 'Show trends over time'},
        {'type': 'scatter', 'name': 'Scatter Plot', 'description': 'Show relationships'},
        {'type': 'histogram', 'name': 'Histogram', 'description': 'Show distribution'},
        {'type': 'box_plot', 'name': 'Box Plot', 'description': 'Show statistical summary'},
        {'type': 'heatmap', 'name': 'Heatmap', 'description': 'Show correlations'}
    ]
    
    return jsonify({'chart_types': chart_types}), 200
