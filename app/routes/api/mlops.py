"""
FINESE2 - MLOps API Routes
Handles MLOps operations using the consolidated MLOps module.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import time
from app.core.mlops import mlops_manager
from app.core.ml_models import ml_model_manager
from app.core.data import data_manager

logger = logging.getLogger(__name__)

mlops_bp = Blueprint('api_mlops', __name__)


@mlops_bp.route('/experiments', methods=['POST'])
@jwt_required()
def create_experiment():
    """Create a new experiment."""
    try:
        user_id = get_jwt_identity()
        experiment_name = request.json.get('name', f'Experiment_{user_id}_{int(time.time())}')
        description = request.json.get('description', '')
        
        experiment_id = mlops_manager.start_experiment(experiment_name, description)
        
        return jsonify({
            'success': True,
            'experiment_id': experiment_id,
            'name': experiment_name
        }), 200
        
    except Exception as e:
        logger.error(f"Creating experiment failed: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/experiments', methods=['GET'])
@jwt_required()
def get_experiments():
    """Get list of experiments."""
    try:
        user_id = get_jwt_identity()
        experiment_name = request.args.get('name')
        
        experiments = mlops_manager.get_experiment_history(experiment_name)
        
        return jsonify({
            'success': True,
            'experiments': experiments
        }), 200
        
    except Exception as e:
        logger.error(f"Getting experiments failed: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/experiments/<experiment_id>', methods=['PUT'])
@jwt_required()
def update_experiment(experiment_id):
    """Update an experiment with metrics or parameters."""
    try:
        user_id = get_jwt_identity()
        metrics = request.json.get('metrics', {})
        parameters = request.json.get('parameters', {})
        
        # Log metrics and parameters
        for metric_name, value in metrics.items():
            mlops_manager.log_metric(metric_name, value)
        
        for param_name, value in parameters.items():
            mlops_manager.log_parameter(param_name, value)
        
        return jsonify({
            'success': True,
            'experiment_id': experiment_id
        }), 200
        
    except Exception as e:
        logger.error(f"Updating experiment failed: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/models', methods=['POST'])
@jwt_required()
def register_model():
    """Register a model in the model registry."""
    try:
        user_id = get_jwt_identity()
        model_data = request.json.get('model_data')  # In a real app, this would be a model ID or path
        model_name = request.json.get('name', f'Model_{user_id}_{int(time.time())}')
        version = request.json.get('version', '1.0')
        metrics = request.json.get('metrics', {})
        description = request.json.get('description', '')
        
        # In a real implementation, you would load the actual model
        # For now, we'll simulate registering a model
        model_id = mlops_manager.register_model(
            model=None,  # Placeholder - in real app would be actual model object
            model_name=model_name,
            version=version,
            metrics=metrics,
            description=description
        )
        
        return jsonify({
            'success': True,
            'model_id': model_id,
            'model_name': model_name
        }), 200
        
    except Exception as e:
        logger.error(f"Registering model failed: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/models', methods=['GET'])
@jwt_required()
def get_models():
    """Get list of registered models."""
    try:
        user_id = get_jwt_identity()
        models = mlops_manager.get_leaderboard(top_n=20)  # Get top 20 models
        
        return jsonify({
            'success': True,
            'models': models
        }), 200
        
    except Exception as e:
        logger.error(f"Getting models failed: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/models/<int:model_id>/promote', methods=['POST'])
@jwt_required()
def promote_model(model_id):
    """Promote model to production."""
    try:
        user_id = get_jwt_identity()
        new_status = request.json.get('status', 'production')
        
        result = mlops_service.promote_model(
            model_id=model_id,
            user_id=user_id,
            new_status=new_status
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to promote model: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    """Get model leaderboard."""
    try:
        user_id = get_jwt_identity()
        top_n = int(request.args.get('top_n', 10))
        
        leaderboard = mlops_manager.get_leaderboard(top_n=top_n)
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        }), 200
        
    except Exception as e:
        logger.error(f"Getting leaderboard failed: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/models/compare', methods=['POST'])
@jwt_required()
def compare_models():
    """Compare multiple models."""
    try:
        user_id = get_jwt_identity()
        model_ids = request.json.get('model_ids', [])
        metric = request.json.get('metric', 'accuracy')
        
        if not model_ids:
            return jsonify({'error': 'Model IDs required'}), 400
        
        comparisons = mlops_manager.compare_models(model_ids, metric)
        
        return jsonify({
            'success': True,
            'comparisons': comparisons
        }), 200
        
    except Exception as e:
        logger.error(f"Comparing models failed: {e}")
        return jsonify({'error': str(e)}), 500
