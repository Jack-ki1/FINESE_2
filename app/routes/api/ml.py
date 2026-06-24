"""
FINESE2 - ML Models API Routes
Handles machine learning operations using the consolidated ML models module.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.core.ml_models import ml_model_manager
from app.core.data import data_manager
from app.core.mlops import mlops_manager

logger = logging.getLogger(__name__)

ml_bp = Blueprint('api_ml', __name__)


@ml_bp.route('/train', methods=['POST'])
@jwt_required()
def train_model():
    """Train a machine learning model."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        model_type = request.json.get('model_type', 'random_forest')
        target_col = request.json.get('target_col')
        problem_type = request.json.get('problem_type', 'auto')
        feature_cols = request.json.get('feature_cols', None)
        test_size = request.json.get('test_size', 0.2)
        
        if not all([dataset_id, target_col]):
            return jsonify({'error': 'Dataset ID and target column required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Start experiment
        experiment_id = mlops_manager.start_experiment(
            f"model_training_{model_type}_{target_col}",
            f"Training {model_type} model for {target_col}"
        )
        
        # Perform training pipeline
        result = ml_model_manager.train_pipeline(
            df, target_col, model_type, problem_type, feature_cols, test_size
        )
        
        model = result['model']
        metrics = result['metrics']
        
        # Log metrics to MLOps manager
        for metric_name, metric_value in metrics.items():
            mlops_manager.log_metric(metric_name, metric_value)
        
        # Register the model
        model_id = mlops_manager.register_model(
            model, 
            f"{model_type}_{target_col}",
            metrics=metrics,
            description=f"Trained {model_type} model for {target_col} prediction"
        )
        
        # End experiment
        mlops_manager.end_experiment()
        
        return jsonify({
            'success': True,
            'model_id': model_id,
            'experiment_id': experiment_id,
            'model_type': model_type,
            'problem_type': problem_type,
            'metrics': metrics,
            'feature_importance': result['feature_importance']
        }), 200
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/predict', methods=['POST'])
@jwt_required()
def make_prediction():
    """Make predictions using a trained model."""
    try:
        user_id = get_jwt_identity()
        model_id = request.json.get('model_id')
        dataset_id = request.json.get('dataset_id')
        
        if not all([model_id, dataset_id]):
            return jsonify({'error': 'Model ID and dataset ID required'}), 400
        
        # Load model
        model = mlops_manager.load_model(model_id)
        
        # Get data
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Prepare data for prediction (same as training preparation)
        feature_cols = [col for col in df.columns if col != 'target']  # Assuming 'target' was the training target
        X, _ = ml_model_manager.prepare_data(df, df.columns[0], feature_cols)  # Using first column as dummy target
        
        # Make predictions
        predictions = ml_model_manager.make_predictions(model, X)
        
        return jsonify({
            'success': True,
            'predictions': predictions.tolist(),
            'count': len(predictions)
        }), 200
        
    except Exception as e:
        logger.error(f"Making predictions failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/compare', methods=['POST'])
@jwt_required()
def compare_models():
    """Compare multiple machine learning models."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        model_types = request.json.get('model_types', ['random_forest', 'logistic_regression'])
        target_col = request.json.get('target_col')
        problem_type = request.json.get('problem_type', 'auto')
        feature_cols = request.json.get('feature_cols', None)
        
        if not all([dataset_id, target_col]):
            return jsonify({'error': 'Dataset ID and target column required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Prepare data
        X, y = ml_model_manager.prepare_data(df, target_col, feature_cols)
        X_train, X_test, y_train, y_test = ml_model_manager.split_data(X, y)
        
        # Compare models
        comparison_results = ml_model_manager.compare_models(
            X_train, y_train, X_test, y_test, model_types, problem_type
        )
        
        # Format results for response
        formatted_results = {}
        for model_type, result in comparison_results.items():
            if 'error' not in result:
                formatted_results[model_type] = {
                    'metrics': result['metrics'],
                    'cross_validation': result['cross_validation']
                }
            else:
                formatted_results[model_type] = result
        
        return jsonify({
            'success': True,
            'comparison_results': formatted_results,
            'best_model': max(
                [(k, v['metrics'].get('accuracy', v['metrics'].get('r2_score', 0))) 
                 for k, v in formatted_results.items() if 'error' not in v],
                key=lambda x: x[1],
                default=(None, None)
            )[0] if any('error' not in v for v in formatted_results.values()) else None
        }), 200
        
    except Exception as e:
        logger.error(f"Model comparison failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/models/types', methods=['GET'])
@jwt_required()
def get_model_types():
    """Get available model types."""
    try:
        user_id = get_jwt_identity()
        
        available_models = ml_model_manager.get_available_models()
        
        return jsonify({
            'success': True,
            'model_types': available_models
        }), 200
        
    except Exception as e:
        logger.error(f"Getting model types failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/evaluate', methods=['POST'])
@jwt_required()
def evaluate_model():
    """Evaluate a trained model on test data."""
    try:
        user_id = get_jwt_identity()
        model_id = request.json.get('model_id')
        dataset_id = request.json.get('dataset_id')
        target_col = request.json.get('target_col')
        
        if not all([model_id, dataset_id, target_col]):
            return jsonify({'error': 'Model ID, dataset ID, and target column required'}), 400
        
        # Load model
        model = mlops_manager.load_model(model_id)
        
        # Get data
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Prepare data
        X, y = ml_model_manager.prepare_data(df, target_col)
        
        # Determine problem type
        problem_type = ml_model_manager.identify_problem_type(y)
        
        # Evaluate model
        metrics = mlops_manager.evaluate_model_performance(model, X, y, problem_type)
        
        return jsonify({
            'success': True,
            'model_id': model_id,
            'problem_type': problem_type,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}")
        return jsonify({'error': str(e)}), 500