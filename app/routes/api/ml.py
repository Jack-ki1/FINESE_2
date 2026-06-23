"""
FINESE2 - Machine Learning API Routes
Handles model training, prediction, and comparison.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.services.data_service import data_service
from app.services.ml_service import ml_service

logger = logging.getLogger(__name__)

ml_bp = Blueprint('api_ml', __name__)


@ml_bp.route('/train', methods=['POST'])
@jwt_required()
def train_model():
    """Train a machine learning model."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        config = request.json.get('config', {})
        
        if not dataset_id or not config:
            return jsonify({'error': 'Dataset ID and config required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        result = ml_service.train_model(
            df=df,
            config=config,
            user_id=user_id,
            dataset_id=dataset_id
        )
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """Generate predictions using a trained model."""
    try:
        user_id = get_jwt_identity()
        model_id = request.json.get('model_id')
        data = request.json.get('data')
        
        if not model_id or not data:
            return jsonify({'error': 'Model ID and data required'}), 400
        
        import pandas as pd
        df = pd.DataFrame(data)
        
        result = ml_service.get_model_predictions(
            model_id=model_id,
            data=df,
            user_id=user_id
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/compare', methods=['POST'])
@jwt_required()
def compare_models():
    """Compare multiple models/experiments."""
    try:
        user_id = get_jwt_identity()
        experiment_ids = request.json.get('experiment_ids', [])
        
        if not experiment_ids:
            return jsonify({'error': 'Experiment IDs required'}), 400
        
        result = ml_service.compare_models(
            experiment_ids=experiment_ids,
            user_id=user_id
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Model comparison failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/models/types', methods=['GET'])
@jwt_required()
def get_model_types():
    """Get available model types."""
    model_types = {
        'classification': [
            'Logistic Regression', 'Random Forest', 'Gradient Boosting',
            'SVM', 'K-Nearest Neighbors', 'Naive Bayes'
        ],
        'regression': [
            'Linear Regression', 'Ridge', 'Lasso', 'Random Forest',
            'Gradient Boosting', 'SVR'
        ]
    }
    
    return jsonify({'model_types': model_types}), 200
