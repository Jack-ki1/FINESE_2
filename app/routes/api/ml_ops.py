"""
FINESE2 - ML Operations API Routes
Handles machine learning, analysis, and MLOps operations using the consolidated modules.
"""
from flask import Blueprint, request, jsonify
import logging
from app.core.ml_models import ml_model_manager
from app.core.data import data_manager
from app.core.mlops import mlops_manager
from app.core.analysis import statistical_analyzer


logger = logging.getLogger(__name__)

ml_ops_bp = Blueprint('api_ml_ops', __name__)


@ml_ops_bp.route('/train', methods=['POST'])
def train_model():
    """Train a machine learning model."""
    try:
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


@ml_ops_bp.route('/predict', methods=['POST'])
def make_prediction():
    """Make predictions using a trained model."""
    try:
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
        target_col = request.json.get('target_col', None)
        feature_cols = request.json.get('feature_cols', None)
        
        # Make predictions
        predictions = ml_model_manager.make_predictions(model, df, target_col, feature_cols)
        
        return jsonify({
            'predictions': predictions.tolist(),
            'count': len(predictions)
        }), 200
        
    except Exception as e:
        logger.error(f"Making predictions failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_ops_bp.route('/evaluate', methods=['POST'])
def evaluate_model():
    """Evaluate a trained model."""
    try:
        model_id = request.json.get('model_id')
        dataset_id = request.json.get('dataset_id')
        target_col = request.json.get('target_col')
        
        if not all([model_id, dataset_id, target_col]):
            return jsonify({'error': 'Model ID, dataset ID, and target column required'}), 400
        
        # Load model and data
        model = mlops_manager.load_model(model_id)
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Evaluate model
        evaluation_results = ml_model_manager.evaluate_model(model, df, target_col)
        
        return jsonify(evaluation_results), 200
        
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_ops_bp.route('/experiments', methods=['GET'])
def list_experiments():
    """List all experiments."""
    try:
        experiments = mlops_manager.list_experiments()
        
        return jsonify({'experiments': experiments}), 200
        
    except Exception as e:
        logger.error(f"Listing experiments failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_ops_bp.route('/models', methods=['GET'])
def list_models():
    """List all registered models."""
    try:
        models = mlops_manager.list_models()
        
        return jsonify({'models': models}), 200
        
    except Exception as e:
        logger.error(f"Listing models failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_ops_bp.route('/statistical-test', methods=['POST'])
def perform_statistical_test():
    """Perform statistical analysis/tests."""
    try:
        dataset_id = request.json.get('dataset_id')
        test_type = request.json.get('test_type')
        col1 = request.json.get('col1')
        col2 = request.json.get('col2', None)
        alpha = request.json.get('alpha', 0.05)
        
        if not all([dataset_id, test_type, col1]):
            return jsonify({'error': 'Dataset ID, test type, and column required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Perform statistical test
        result = statistical_analyzer.perform_test(df, test_type, col1, col2, alpha)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Statistical test failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_ops_bp.route('/correlation', methods=['POST'])
def calculate_correlation():
    """Calculate correlation between variables."""
    try:
        dataset_id = request.json.get('dataset_id')
        method = request.json.get('method', 'pearson')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Calculate correlation matrix
        correlation_matrix = statistical_analyzer.calculate_correlation(df, method)
        
        return jsonify({
            'correlation_matrix': correlation_matrix,
            'method': method
        }), 200
        
    except Exception as e:
        logger.error(f"Correlation calculation failed: {e}")
        return jsonify({'error': str(e)}), 500


@ml_ops_bp.route('/hypothesis-test', methods=['POST'])
def hypothesis_test():
    """Perform hypothesis testing."""
    try:
        dataset_id = request.json.get('dataset_id')
        test_type = request.json.get('test_type')
        variable = request.json.get('variable')
        null_hypothesis = request.json.get('null_hypothesis')
        alternative_hypothesis = request.json.get('alternative_hypothesis')
        
        if not all([dataset_id, test_type, variable]):
            return jsonify({'error': 'Dataset ID, test type, and variable required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Perform hypothesis test
        result = statistical_analyzer.hypothesis_test(
            df, test_type, variable, null_hypothesis, alternative_hypothesis
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Hypothesis test failed: {e}")
        return jsonify({'error': str(e)}), 500