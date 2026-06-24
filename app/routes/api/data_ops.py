"""
FINESE2 - Data Operations API Routes
Handles data operations including uploading, cleaning, transformation, and basic analysis.
"""
from flask import Blueprint, request, jsonify, current_app
import logging
from app.core.data import data_manager
from app.core.cleaning import cleaning_manager
from app.core.eda import eda_engine
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

data_ops_bp = Blueprint('api_data_ops', __name__)


@data_ops_bp.route('/upload', methods=['POST'])
def upload_dataset():
    """Upload a new dataset file."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Security check on filename
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        # Save file temporarily
        upload_folder = current_app.config.get('UPLOAD_FOLDER', './uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Load dataset into data manager
        dataset_id = data_manager.load_dataset_from_file(filepath, filename)
        
        # Clean up temporary file
        os.remove(filepath)
        
        return jsonify({
            'dataset_id': dataset_id,
            'filename': filename,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Dataset upload failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/load', methods=['POST'])
def load_dataset():
    """Load dataset from various sources."""
    try:
        source_type = request.json.get('source_type')
        source_config = request.json.get('source_config')
        
        if not all([source_type, source_config]):
            return jsonify({'error': 'Source type and config required'}), 400
        
        # Load dataset based on source type
        dataset_id = data_manager.load_dataset_from_source(source_type, source_config)
        
        return jsonify({
            'dataset_id': dataset_id,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Loading dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/datasets', methods=['GET'])
def list_datasets():
    """List all available datasets (UI contract)."""
    try:
        datasets = data_manager.list_datasets()

        # UI expects: { id, name/filename, file_type, rows, columns, size_mb, created_at }
        out = []
        for d in datasets:
            dataset_id = d.get('dataset_id')
            out.append({
                'id': dataset_id,
                'name': dataset_id,
                'filename': d.get('dataset_id'),
                'file_type': 'parquet',
                'rows': d.get('rows'),
                'columns': d.get('columns'),
                'size_mb': None,
                'created_at': d.get('upload_time')
            })

        return jsonify({'datasets': out}), 200

    except Exception as e:
        logger.error(f"Listing datasets failed: {e}")
        return jsonify({'error': str(e)}), 500



@data_ops_bp.route('/dataset/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """Get dataset information (UI contract).

    UI uses this as a metadata call for columns.
    """
    try:
        dataset_info = data_manager.get_dataset_info(dataset_id)
        if dataset_info is None:
            return jsonify({'error': 'Dataset not found'}), 404

        # UI expects: { columns: [...] }
        return jsonify({
            'columns': dataset_info.get('columns', []),
            'dtypes': dataset_info.get('dtypes', {}),
            'shape': dataset_info.get('shape'),
            'missing_values': dataset_info.get('missing_values', {}),
            'duplicate_rows': dataset_info.get('duplicate_rows')
        }), 200

    except Exception as e:
        logger.error(f"Getting dataset info failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/preview/<dataset_id>', methods=['GET'])
def preview_dataset(dataset_id):
    """Preview dataset content."""
    try:
        preview_data = data_manager.preview_dataset(dataset_id)
        
        if preview_data is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        return jsonify(preview_data), 200
        
    except Exception as e:
        logger.error(f"Previewing dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/clean', methods=['POST'])
def clean_dataset():
    """Clean dataset using various cleaning techniques."""
    try:
        dataset_id = request.json.get('dataset_id')
        cleaning_operations = request.json.get('operations', [])
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Apply cleaning operations
        cleaned_df = cleaning_manager.apply_cleaning_operations(df, cleaning_operations)
        
        # Update the dataset with cleaned data
        data_manager.update_dataset(dataset_id, cleaned_df)
        
        return jsonify({
            'success': True,
            'cleaning_summary': cleaning_manager.get_cleaning_summary()
        }), 200
        
    except Exception as e:
        logger.error(f"Cleaning dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/transform', methods=['POST'])
def transform_dataset():
    """Transform dataset using various transformations."""
    try:
        dataset_id = request.json.get('dataset_id')
        transformations = request.json.get('transformations', [])
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Apply transformations
        transformed_df = data_manager.apply_transformations(df, transformations)
        
        # Update the dataset with transformed data
        data_manager.update_dataset(dataset_id, transformed_df)
        
        return jsonify({
            'success': True,
            'transformations_applied': transformations
        }), 200
        
    except Exception as e:
        logger.error(f"Transforming dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/describe/<dataset_id>', methods=['GET'])
def describe_dataset(dataset_id):
    """Get dataset descriptive statistics (legacy)."""
    try:
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404

        # Use EDA engine basic statistics
        stats = eda_engine.load_data(df).basic_statistics()
        return jsonify({'success': True, 'basic_stats': stats}), 200

    except Exception as e:
        logger.error(f"Describing dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/sample', methods=['POST'])
def load_sample():
    """Load a built-in sample dataset (UI contract)."""
    try:
        body = request.get_json(silent=True) or {}
        name = body.get('name')
        if not name:
            return jsonify({'error': 'name is required'}), 400

        df = data_manager.load_sample_dataset(name)

        # Register dataset in DataManager
        # DataManager expects file-based upload to generate IDs, but we can create an ID deterministically.
        import hashlib
        dataset_id = hashlib.md5(f"sample_{name}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        data_manager._set_dataset(
            dataset_id=dataset_id,
            df=df,
            user_id=0,
            metadata=data_manager._generate_metadata(df),
            lineage={'source': {'type': 'sample', 'name': name}, 'transformations': []},
            version=1
        )

        return jsonify({'success': True, 'dataset_id': dataset_id, 'name': name}), 200

    except Exception as e:
        logger.error(f"Loading sample dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/info/<dataset_id>', methods=['GET'])
def dataset_info(dataset_id):
    """Get dataset information (legacy)."""
    try:
        info = data_manager.get_dataset_info(dataset_id)
        if info is None:
            return jsonify({'error': 'Dataset not found'}), 404
        return jsonify({'success': True, 'info': info}), 200

    except Exception as e:
        logger.error(f"Getting dataset info failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/datasets/<dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    """Delete dataset (UI contract)."""
    try:
        ok = data_manager.delete_dataset(dataset_id)
        if not ok:
            return jsonify({'error': 'Dataset not found'}), 404
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Deleting dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/cleaning/apply', methods=['POST'])
def apply_cleaning():
    """Apply cleaning operations to a dataset."""
    try:
        dataset_id = request.json.get('dataset_id')
        operations = request.json.get('operations', {})
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Apply cleaning operations using the correct method
        cleaned_df = cleaning_manager.clean_dataset(df, [operations])
        
        # Get cleaning summary
        summary = cleaning_manager.get_cleaning_summary()
        
        # Save cleaned dataset
        cleaned_id = data_manager.save_dataset(
            cleaned_df,
            f"{dataset_id}_cleaned",
            'Cleaned dataset'
        )
        
        return jsonify({
            'success': True,
            'cleaning_results': {
                **summary,
                'new_shape': list(cleaned_df.shape),
                'rows_removed': len(df) - len(cleaned_df)
            },
            'cleaned_dataset_id': cleaned_id
        }), 200
        
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/visualization/create', methods=['POST'])
def create_visualization():
    """Create visualization for a dataset."""
    try:
        from app.core.visualize import visualizer
        
        dataset_id = request.json.get('dataset_id')
        chart_type = request.json.get('chart_type', 'scatter')
        x_col = request.json.get('x_col')
        y_col = request.json.get('y_col')
        color_col = request.json.get('color_col')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Create visualization
        fig = visualizer.create_chart(df, chart_type, x_col, y_col, color_col)
        
        # Convert to JSON for frontend
        chart_json = fig.to_json() if hasattr(fig, 'to_json') else None
        
        return jsonify({
            'success': True,
            'chart_json': chart_json,
            'chart_type': chart_type
        }), 200
        
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        return jsonify({'error': str(e)}), 500


@data_ops_bp.route('/analysis/descriptive', methods=['POST'])
def descriptive_analysis():
    """Perform descriptive statistical analysis."""
    try:
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Perform descriptive analysis using the correct method name
        results = statistical_analyzer.descriptive_statistics(df)
        
        return jsonify({
            'success': True,
            'analysis_results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Descriptive analysis failed: {e}")
        return jsonify({'error': str(e)}), 500
