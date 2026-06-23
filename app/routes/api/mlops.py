"""
FINESE2 - MLOps API Routes
Handles experiment tracking, model registry, and leaderboard.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.services.mlops_service import mlops_service

logger = logging.getLogger(__name__)

mlops_bp = Blueprint('api_mlops', __name__)


@mlops_bp.route('/experiments', methods=['POST'])
@jwt_required()
def create_experiment():
    """Create a new experiment."""
    try:
        user_id = get_jwt_identity()
        name = request.json.get('name')
        description = request.json.get('description', '')
        dataset_id = request.json.get('dataset_id')
        params = request.json.get('params', {})
        
        if not name:
            return jsonify({'error': 'Experiment name required'}), 400
        
        result = mlops_service.create_experiment(
            name=name,
            description=description,
            user_id=user_id,
            dataset_id=dataset_id,
            params=params
        )
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/experiments', methods=['GET'])
@jwt_required()
def list_experiments():
    """List user's experiments."""
    try:
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status')
        
        experiments = mlops_service.get_experiments(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status
        )
        
        return jsonify({'experiments': experiments}), 200
        
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/experiments/<int:experiment_id>', methods=['PUT'])
@jwt_required()
def update_experiment(experiment_id):
    """Update experiment with results."""
    try:
        user_id = get_jwt_identity()
        metrics = request.json.get('metrics')
        status = request.json.get('status')
        duration_ms = request.json.get('duration_ms')
        
        result = mlops_service.update_experiment(
            experiment_id=experiment_id,
            user_id=user_id,
            metrics=metrics,
            status=status,
            duration_ms=duration_ms
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to update experiment: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/models', methods=['POST'])
@jwt_required()
def register_model():
    """Register a model in the registry."""
    try:
        user_id = get_jwt_identity()
        name = request.json.get('name')
        version = request.json.get('version', '1.0')
        experiment_id = request.json.get('experiment_id')
        model_type = request.json.get('model_type')
        problem_type = request.json.get('problem_type')
        metrics = request.json.get('metrics', {})
        tags = request.json.get('tags', [])
        
        if not name or not experiment_id:
            return jsonify({'error': 'Name and experiment ID required'}), 400
        
        result = mlops_service.register_model(
            name=name,
            version=version,
            experiment_id=experiment_id,
            user_id=user_id,
            model_type=model_type,
            problem_type=problem_type,
            metrics=metrics,
            tags=tags
        )
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Failed to register model: {e}")
        return jsonify({'error': str(e)}), 500


@mlops_bp.route('/models', methods=['GET'])
@jwt_required()
def list_models():
    """List user's models."""
    try:
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status')
        
        models = mlops_service.get_models(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status
        )
        
        return jsonify({'models': models}), 200
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
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
        metric = request.args.get('metric', 'accuracy')
        problem_type = request.args.get('problem_type')
        limit = int(request.args.get('limit', 10))
        
        leaderboard = mlops_service.get_leaderboard(
            user_id=user_id,
            metric=metric,
            problem_type=problem_type,
            limit=limit
        )
        
        return jsonify({'leaderboard': leaderboard}), 200
        
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}")
        return jsonify({'error': str(e)}), 500
