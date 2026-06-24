"""
FINESE2 - Analysis API Routes
Handles statistical analysis operations using the consolidated analysis module.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.core.analysis import analysis_engine
from app.core.data import data_manager

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('api_analysis', __name__)


@analysis_bp.route('/perform', methods=['POST'])
@jwt_required()
def perform_analysis():
    """Perform analysis based on the request parameters."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        analysis_type = request.json.get('analysis_type', 'descriptive')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Perform analysis based on type
        if analysis_type == 'descriptive':
            result = analysis_engine.descriptive_statistics(df)
        elif analysis_type == 'correlation':
            method = request.json.get('method', 'pearson')
            result = analysis_engine.correlation_analysis(df, method)
        elif analysis_type == 'regression':
            target_col = request.json.get('target_col')
            feature_cols = request.json.get('feature_cols')
            result = analysis_engine.regression_analysis(df, target_col, feature_cols)
        elif analysis_type == 'hypothesis_test':
            test_type = request.json.get('test_type')
            group_col = request.json.get('group_col')
            value_col = request.json.get('value_col')
            result = analysis_engine.hypothesis_tests(df, test_type, group_col, value_col)
        elif analysis_type == 'time_series':
            date_col = request.json.get('date_col')
            value_col = request.json.get('value_col')
            result = analysis_engine.time_series_analysis(df, date_col, value_col)
        elif analysis_type == 'feature_importance':
            target_col = request.json.get('target_col')
            method = request.json.get('method', 'correlation')
            result = analysis_engine.feature_importance_analysis(df, target_col, method)
        elif analysis_type == 'outlier_detection':
            method = request.json.get('method', 'iqr')
            result = analysis_engine.outlier_detection_analysis(df, method)
        else:
            return jsonify({'error': f'Analysis type {analysis_type} not supported'}), 400
        
        return jsonify({
            'success': True,
            'analysis_type': analysis_type,
            'result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_analysis_templates():
    """Get available analysis templates."""
    try:
        user_id = get_jwt_identity()
        
        templates = [
            {
                'name': 'descriptive_statistics',
                'title': 'Descriptive Statistics',
                'description': 'Summary statistics for numerical and categorical variables',
                'parameters': ['dataset_id']
            },
            {
                'name': 'correlation_analysis',
                'title': 'Correlation Analysis',
                'description': 'Relationships between numerical variables',
                'parameters': ['dataset_id', 'method']
            },
            {
                'name': 'regression_analysis',
                'title': 'Regression Analysis',
                'description': 'Predictive modeling between target and features',
                'parameters': ['dataset_id', 'target_col', 'feature_cols']
            },
            {
                'name': 'hypothesis_testing',
                'title': 'Hypothesis Testing',
                'description': 'Statistical tests for group differences',
                'parameters': ['dataset_id', 'test_type', 'group_col', 'value_col']
            },
            {
                'name': 'time_series_analysis',
                'title': 'Time Series Analysis',
                'description': 'Temporal pattern analysis',
                'parameters': ['dataset_id', 'date_col', 'value_col']
            },
            {
                'name': 'feature_importance',
                'title': 'Feature Importance',
                'description': 'Ranking of features by importance to target',
                'parameters': ['dataset_id', 'target_col', 'method']
            },
            {
                'name': 'outlier_detection',
                'title': 'Outlier Detection',
                'description': 'Identification of unusual observations',
                'parameters': ['dataset_id', 'method']
            }
        ]
        
        return jsonify({'templates': templates}), 200
        
    except Exception as e:
        logger.error(f"Getting analysis templates failed: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/hypothesis-test', methods=['POST'])
@jwt_required()
def perform_hypothesis_test():
    """Perform a specific hypothesis test."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        test_type = request.json.get('test_type')
        group_col = request.json.get('group_col')
        value_col = request.json.get('value_col')
        
        if not all([dataset_id, test_type, group_col, value_col]):
            return jsonify({'error': 'Dataset ID, test type, group column, and value column required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        result = analysis_engine.hypothesis_tests(df, test_type, group_col, value_col)
        
        return jsonify({
            'success': True,
            'test_type': test_type,
            'result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Hypothesis test failed: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/feature-importance', methods=['POST'])
@jwt_required()
def analyze_feature_importance():
    """Analyze feature importance."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        target_col = request.json.get('target_col')
        method = request.json.get('method', 'correlation')
        
        if not all([dataset_id, target_col]):
            return jsonify({'error': 'Dataset ID and target column required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        result = analysis_engine.feature_importance_analysis(df, target_col, method)
        
        return jsonify({
            'success': True,
            'method': method,
            'result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Feature importance analysis failed: {e}")
        return jsonify({'error': str(e)}), 500