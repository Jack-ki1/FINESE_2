"""
FINESE2 - Data API Routes
Handles dataset upload, download, and management with authentication.
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import pandas as pd
import logging
import io
from app.services.data_service import data_service
from app.services.data_processing_service import data_processing_service

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
        
        # Get optional parameters
        sample_if_large = request.form.get('sample_if_large', 'true').lower() == 'true'
        max_rows = int(request.form.get('max_rows', 10000))
        
        # Upload file using service
        result = data_service.upload_file(
            file=file,
            user_id=user_id,
            filename=file.filename,
            sample_if_large=sample_if_large,
            max_rows=max_rows
        )
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/datasets', methods=['GET'])
@jwt_required()
def list_datasets():
    """List all datasets for current user."""
    try:
        user_id = get_jwt_identity()
        datasets = data_service.get_user_datasets(user_id)
        
        return jsonify({'datasets': datasets}), 200
        
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/datasets/<int:dataset_id>', methods=['GET'])
@jwt_required()
def get_dataset(dataset_id):
    """Get dataset metadata."""
    try:
        user_id = get_jwt_identity()
        dataset = data_service.get_dataset(dataset_id, user_id)
        
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        return jsonify({'dataset': dataset}), 200
        
    except Exception as e:
        logger.error(f"Failed to get dataset: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/datasets/<int:dataset_id>/preview', methods=['GET'])
@jwt_required()
def preview_dataset(dataset_id):
    """Get dataset preview (first N rows)."""
    try:
        user_id = get_jwt_identity()
        rows = int(request.args.get('rows', 10))
        
        preview = data_processing_service.get_dataset_preview(dataset_id, user_id, rows)
        
        if not preview:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        return jsonify({'preview': preview}), 200
        
    except Exception as e:
        logger.error(f"Failed to preview dataset: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/datasets/<int:dataset_id>/download', methods=['GET'])
@jwt_required()
def download_dataset(dataset_id):
    """Download dataset in specified format."""
    try:
        user_id = get_jwt_identity()
        format_type = request.args.get('format', 'csv')
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Export based on format
        if format_type == 'csv':
            csv_bytes = data_processing_service.export_to_csv(df)
            return send_file(
                io.BytesIO(csv_bytes),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'dataset_{dataset_id}.csv'
            )
        elif format_type == 'excel':
            excel_bytes = data_processing_service.export_to_excel(df)
            return send_file(
                io.BytesIO(excel_bytes),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'dataset_{dataset_id}.xlsx'
            )
        elif format_type == 'json':
            json_bytes = data_processing_service.export_to_json(df)
            return send_file(
                io.BytesIO(json_bytes),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'dataset_{dataset_id}.json'
            )
        else:
            return jsonify({'error': f'Unsupported format: {format_type}'}), 400
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/datasets/<int:dataset_id>', methods=['DELETE'])
@jwt_required()
def delete_dataset(dataset_id):
    """Delete a dataset."""
    try:
        user_id = get_jwt_identity()
        success = data_service.delete_dataset(dataset_id, user_id)
        
        if not success:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        return jsonify({'message': 'Dataset deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Failed to delete dataset: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/sample-dataset/<string:dataset_name>', methods=['POST'])
@jwt_required()
def sample_dataset_compat(dataset_name: str):
    """Compatibility endpoint used by the dashboard UI."""
    try:
        user_id = get_jwt_identity()
        result = data_service.load_sample_dataset(dataset_name, user_id)
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Failed to load sample dataset: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/load-sample', methods=['POST'])
@jwt_required()
def load_sample_dataset():
    """Load a built-in sample dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_name = request.json.get('dataset_name')
        
        if not dataset_name:
            return jsonify({'error': 'Dataset name required'}), 400
        
        result = data_service.load_sample_dataset(dataset_name, user_id)
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Failed to load sample dataset: {e}")
        return jsonify({'error': str(e)}), 500
