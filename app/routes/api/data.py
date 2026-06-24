"""
FINESE2 - Consolidated Data API Routes
Handles all data-related operations using the consolidated data module.
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import os
import tempfile
from app.core.data import data_manager

logger = logging.getLogger(__name__)

data_bp = Blueprint('api_data', __name__)


@data_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_dataset():
    """Upload a dataset file."""
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        
        # Upload to data manager
        result = data_manager.upload_dataset(temp_file.name, user_id)
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Dataset upload failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/datasets', methods=['GET'])
@jwt_required()
def list_datasets():
    """List user's datasets."""
    try:
        user_id = get_jwt_identity()
        # For now, return a placeholder since our data manager doesn't track user datasets separately
        return jsonify({'datasets': []}), 200
        
    except Exception as e:
        logger.error(f"Listing datasets failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/datasets/<dataset_id>', methods=['GET'])
@jwt_required()
def get_dataset_info(dataset_id):
    """Get dataset information."""
    try:
        info = data_manager.get_dataset_info(dataset_id)
        if info is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        return jsonify(info), 200
        
    except Exception as e:
        logger.error(f"Getting dataset info failed: {e}")
        return jsonify({'error': str(e)}), 500




@data_bp.route('/export/<dataset_id>', methods=['POST'])
@jwt_required()
def export_dataset(dataset_id):
    """Export dataset in specified format."""
    try:
        format_type = request.json.get('format', 'csv')
        
        file_path = data_manager.export_dataset(dataset_id, format_type)
        
        return jsonify({'file_path': file_path}), 200
        
    except Exception as e:
        logger.error(f"Exporting dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/datasets/<dataset_id>', methods=['DELETE'])
@jwt_required()
def delete_dataset(dataset_id):
    """Delete a dataset."""
    try:
        success = data_manager.delete_dataset(dataset_id)
        if not success:
            return jsonify({'error': 'Dataset not found'}), 404
        
        return jsonify({'message': 'Dataset deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Deleting dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/load-sample', methods=['POST'])
@jwt_required()
def load_sample():
    """Load a sample dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_name = request.json.get('name', 'iris')
        
        df = data_manager.load_sample_dataset(dataset_name)
        dataset_id = f"sample_{dataset_name}_{user_id}"
        
        # Add to data manager
        data_manager.datasets[dataset_id] = {
            'df': df,
            'user_id': user_id,
            'upload_time': None,
            'file_path': f"sample_{dataset_name}",
            'metadata': data_manager._generate_metadata(df)
        }
        
        result = {
            'dataset_id': dataset_id,
            'rows': len(df),
            'columns': len(df.columns),
            'columns_list': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'size_mb': 0  # Sample datasets don't have file size
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Loading sample dataset failed: {e}")
        return jsonify({'error': str(e)}), 500
