"""
FINESE2 - Consolidated EDA API Routes
Handles all EDA operations using the consolidated EDA module.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.core.eda import eda_engine
from app.core.data import data_manager

logger = logging.getLogger(__name__)

eda_bp = Blueprint('api_eda', __name__)


@eda_bp.route('/profile', methods=['POST'])
@jwt_required()
def generate_profile():
    """Generate comprehensive EDA profile."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Load data into EDA engine and generate profile
        profile = eda_engine.load_data(df).generate_profile_report()
        
        return jsonify(profile), 200
        
    except Exception as e:
        logger.error(f"EDA profile generation failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/issues', methods=['POST'])
@jwt_required()
def detect_issues():
    """Detect data quality issues."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Load data into EDA engine and detect issues
        issues = eda_engine.load_data(df).missing_values_analysis()
        
        return jsonify(issues), 200
        
    except Exception as e:
        logger.error(f"EDA issues detection failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/distribution/<column>', methods=['POST'])
@jwt_required()
def analyze_distribution(column):
    """Analyze distribution of a specific column."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Load data into EDA engine and analyze distribution
        distribution = eda_engine.load_data(df).distribution_analysis(column)
        
        return jsonify(distribution), 200
        
    except Exception as e:
        logger.error(f"EDA distribution analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/correlation', methods=['POST'])
@jwt_required()
def analyze_correlation():
    """Analyze correlations in the dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        method = request.json.get('method', 'pearson')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Load data into EDA engine and analyze correlation
        correlation = eda_engine.load_data(df).correlation_analysis(method)
        
        return jsonify(correlation), 200
        
    except Exception as e:
        logger.error(f"EDA correlation analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/missing-pattern', methods=['POST'])
@jwt_required()
def analyze_missing_patterns():
    """Analyze missing value patterns."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Load data into EDA engine and analyze missing patterns
        missing_analysis = eda_engine.load_data(df).missing_values_analysis()
        
        return jsonify(missing_analysis), 200
        
    except Exception as e:
        logger.error(f"EDA missing patterns analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/ydata-report', methods=['POST'])
@jwt_required()
def generate_ydata_report():
    """Generate YData-style report."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Generate a simplified version of the profile report
        profile = eda_engine.load_data(df).generate_profile_report()
        
        return jsonify(profile), 200
        
    except Exception as e:
        logger.error(f"YData report generation failed: {e}")
        return jsonify({'error': str(e)}), 500
