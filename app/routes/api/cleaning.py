"""
FINESE2 - Data Cleaning API Routes
Handles data cleaning operations and recommendations.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.services.data_service import data_service
from app.services.cleaning_service import cleaning_service

logger = logging.getLogger(__name__)

cleaning_bp = Blueprint('api_cleaning', __name__)


@cleaning_bp.route('/recommendations', methods=['POST'])
@jwt_required()
def get_recommendations():
    """Get smart cleaning recommendations."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        recommendations = cleaning_service.get_cleaning_recommendations(df)
        
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        return jsonify({'error': str(e)}), 500


@cleaning_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_cleaning():
    """Apply cleaning operations to dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        operations = request.json.get('operations', [])
        
        if not dataset_id or not operations:
            return jsonify({'error': 'Dataset ID and operations required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        cleaned_df, summary = cleaning_service.apply_cleaning(
            df=df,
            operations=operations,
            user_id=user_id,
            dataset_id=dataset_id
        )
        
        # Save cleaned dataset
        result = data_service.save_cleaned_dataset(
            cleaned_df, user_id, dataset_id, summary
        )
        
        return jsonify({
            'summary': summary,
            'new_dataset_id': result.get('dataset_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        return jsonify({'error': str(e)}), 500
