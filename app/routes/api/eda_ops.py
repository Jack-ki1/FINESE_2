"""
FINESE2 - EDA Operations API Routes
Handles exploratory data analysis operations and profiling.
"""
from flask import Blueprint, request, jsonify
import logging
import json
import numpy as np
import pandas as pd
from app.core.eda import eda_engine
from app.core.data import data_manager

logger = logging.getLogger(__name__)

eda_ops_bp = Blueprint('api_eda_ops', __name__)


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (pd.Timestamp,)):
            return obj.isoformat()
        elif hasattr(obj, 'dtype'):
            return str(obj.dtype)
        return super().default(obj)


def make_json_serializable(obj):
    """Recursively convert numpy/pandas types to JSON serializable types."""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif hasattr(obj, 'dtype'):
        return str(obj.dtype)
    elif pd.isna(obj):
        return None
    return obj


@eda_ops_bp.route('/profile', methods=['POST'])
def profile_dataset():
    """Generate comprehensive EDA profile for a dataset."""
    try:
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Generate EDA profile
        profile = eda_engine.load_data(df).generate_profile_report()
        
        # Make profile JSON serializable
        profile = make_json_serializable(profile)
        
        return jsonify({
            'success': True,
            'profile': profile
        }), 200
        
    except Exception as e:
        logger.error(f"Profiling dataset failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_ops_bp.route('/correlation', methods=['POST'])
def analyze_correlation():
    """Analyze correlation between features in a dataset."""
    try:
        dataset_id = request.json.get('dataset_id')
        method = request.json.get('method', 'pearson')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Perform correlation analysis
        correlation_results = eda_engine.load_data(df).correlation_analysis(method=method)
        
        return jsonify({
            'success': True,
            'correlation': correlation_results
        }), 200
        
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_ops_bp.route('/missing-values', methods=['POST'])
def analyze_missing_values():
    """Analyze missing values in a dataset."""
    try:
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Analyze missing values
        missing_results = eda_engine.load_data(df).missing_values_analysis()
        
        return jsonify({
            'success': True,
            'missing_values': missing_results
        }), 200
        
    except Exception as e:
        logger.error(f"Missing values analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_ops_bp.route('/distributions', methods=['POST'])
def analyze_distributions():
    """Analyze distributions of features in a dataset."""
    try:
        dataset_id = request.json.get('dataset_id')
        column = request.json.get('column')  # Optional: specific column
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Analyze distributions
        dist_results = eda_engine.load_data(df).distribution_analysis(column=column)
        
        return jsonify({
            'success': True,
            'distributions': dist_results
        }), 200
        
    except Exception as e:
        logger.error(f"Distribution analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_ops_bp.route('/anomalies', methods=['POST'])
def detect_anomalies():
    """Detect anomalies in a dataset."""
    try:
        dataset_id = request.json.get('dataset_id')
        contamination = request.json.get('contamination', 0.1)
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Detect anomalies
        anomaly_results = eda_engine.load_data(df).detect_anomalies(contamination=contamination)
        
        return jsonify({
            'success': True,
            'anomalies': anomaly_results
        }), 200
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        return jsonify({'error': str(e)}), 500
