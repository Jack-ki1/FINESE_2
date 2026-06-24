"""
FINESE2 - Consolidated Data Cleaning API Routes
Handles all data cleaning operations using the consolidated cleaning module.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.core.cleaning import cleaning_manager
from app.core.data import data_manager

logger = logging.getLogger(__name__)

cleaning_bp = Blueprint('api_cleaning', __name__)


@cleaning_bp.route('/recommendations', methods=['POST'])
@jwt_required()
def get_recommendations():
    """Get cleaning recommendations for a dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Get cleaning recommendations
        recommendations = cleaning_manager.get_cleaning_recommendations(df)
        
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        logger.error(f"Cleaning recommendations failed: {e}")
        return jsonify({'error': str(e)}), 500


@cleaning_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_cleaning():
    """Apply cleaning operations to a dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        operations = request.json.get('operations', [])
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Apply cleaning operations
        cleaned_df = cleaning_manager.clean_dataset(df, operations)
        
        # Store cleaned dataset
        data_manager.datasets[dataset_id]['df'] = cleaned_df
        data_manager.datasets[dataset_id]['metadata'] = data_manager._generate_metadata(cleaned_df)
        
        # Return summary of changes
        original_shape = df.shape
        cleaned_shape = cleaned_df.shape
        
        return jsonify({
            'original_shape': original_shape,
            'cleaned_shape': cleaned_shape,
            'rows_removed': original_shape[0] - cleaned_shape[0],
            'columns_removed': original_shape[1] - cleaned_shape[1],
            'operations_applied': len(operations)
        }), 200
        
    except Exception as e:
        logger.error(f"Applying cleaning operations failed: {e}")
        return jsonify({'error': str(e)}), 500


@cleaning_bp.route('/impute', methods=['POST'])
@jwt_required()
def impute_missing():
    """Impute missing values in a dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        strategy = request.json.get('strategy', 'mean')
        columns = request.json.get('columns', None)
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Impute missing values
        imputed_df = cleaning_manager.impute_missing_values(df, strategy, columns)
        
        # Store imputed dataset
        data_manager.datasets[dataset_id]['df'] = imputed_df
        data_manager.datasets[dataset_id]['metadata'] = data_manager._generate_metadata(imputed_df)
        
        # Return summary
        missing_before = df.isnull().sum().sum()
        missing_after = imputed_df.isnull().sum().sum()
        
        return jsonify({
            'missing_values_before': int(missing_before),
            'missing_values_after': int(missing_after),
            'imputed_count': int(missing_before - missing_after),
            'strategy_used': strategy
        }), 200
        
    except Exception as e:
        logger.error(f"Imputing missing values failed: {e}")
        return jsonify({'error': str(e)}), 500


@cleaning_bp.route('/remove-outliers', methods=['POST'])
@jwt_required()
def remove_outliers():
    """Remove outliers from a dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        method = request.json.get('method', 'iqr')
        columns = request.json.get('columns', None)
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Remove outliers
        filtered_df = cleaning_manager.remove_outliers_iqr(df, columns)
        
        # Store filtered dataset
        data_manager.datasets[dataset_id]['df'] = filtered_df
        data_manager.datasets[dataset_id]['metadata'] = data_manager._generate_metadata(filtered_df)
        
        # Return summary
        original_count = len(df)
        filtered_count = len(filtered_df)
        
        return jsonify({
            'original_count': original_count,
            'filtered_count': filtered_count,
            'removed_count': original_count - filtered_count,
            'removal_percentage': round((original_count - filtered_count) / original_count * 100, 2),
            'method_used': method
        }), 200
        
    except Exception as e:
        logger.error(f"Removing outliers failed: {e}")
        return jsonify({'error': str(e)}), 500


@cleaning_bp.route('/normalize', methods=['POST'])
@jwt_required()
def normalize_data():
    """Normalize data in a dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        method = request.json.get('method', 'standard')
        columns = request.json.get('columns', None)
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Normalize data
        normalized_df = cleaning_manager.normalize_data(df, method, columns)
        
        # Store normalized dataset
        data_manager.datasets[dataset_id]['df'] = normalized_df
        data_manager.datasets[dataset_id]['metadata'] = data_manager._generate_metadata(normalized_df)
        
        return jsonify({
            'normalized_columns': columns or df.select_dtypes(include=[float, int]).columns.tolist(),
            'method_used': method
        }), 200
        
    except Exception as e:
        logger.error(f"Normalizing data failed: {e}")
        return jsonify({'error': str(e)}), 500