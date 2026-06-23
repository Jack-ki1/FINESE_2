"""
FINESE2 - EDA API Routes
Handles exploratory data analysis endpoints.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.services.data_service import data_service
from app.services.eda_service import EDASer

logger = logging.getLogger(__name__)

eda_bp = Blueprint('api_eda', __name__)

# EDASer is created per-request/user because it is instantiated with a user_id



@eda_bp.route('/profile', methods=['POST'])
@jwt_required()
def generate_profile():
    """Generate comprehensive EDA profile."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        # Load dataset
        df = data_service.load_dataframe(dataset_id, user_id)

        # Initialize EDA service (user-scoped)
        eda_service = EDASer(str(user_id))

        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Generate profile using engine
        from engine.eda_engine import EDAEngine
        profile = EDAEngine.quick_profile(df)
        
        return jsonify({'profile': profile}), 200
        
    except Exception as e:
        logger.error(f"EDA profiling failed: {e}")
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
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        from engine.eda_engine import EDAEngine
        issues = EDAEngine.detect_issues(df)
        
        return jsonify({'issues': issues}), 200
        
    except Exception as e:
        logger.error(f"Issue detection failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/distribution/<string:column>', methods=['POST'])
@jwt_required()
def get_distribution(column):
    """Get distribution plot for a column."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        from engine.eda_engine import EDAEngine
        fig = EDAEngine.create_distribution_plot(df, column)
        
        return jsonify({'plot': fig.to_json()}), 200
        
    except Exception as e:
        logger.error(f"Distribution plot failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/correlation', methods=['POST'])
@jwt_required()
def get_correlation():
    """Get correlation heatmap."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        from engine.eda_engine import EDAEngine
        fig = EDAEngine.create_correlation_heatmap(df)
        
        if fig is None:
            return jsonify({'error': 'Not enough numeric columns for correlation'}), 400
        
        return jsonify({'plot': fig.to_json()}), 200
        
    except Exception as e:
        logger.error(f"Correlation heatmap failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/missing-pattern', methods=['POST'])
@jwt_required()
def get_missing_pattern():
    """Get missing values pattern heatmap."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        from engine.eda_engine import EDAEngine
        fig = EDAEngine.create_missing_heatmap(df)
        
        return jsonify({'plot': fig.to_json()}), 200
        
    except Exception as e:
        logger.error(f"Missing pattern failed: {e}")
        return jsonify({'error': str(e)}), 500


@eda_bp.route('/ydata-report', methods=['POST'])
@jwt_required()
def generate_ydata_report():
    """Generate ydata-profiling HTML report."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        from engine.eda_engine import EDAEngine
        report_html = EDAEngine.generate_ydata_report(df)
        
        if report_html is None:
            return jsonify({'error': 'Failed to generate report or ydata-profiling not installed'}), 500
        
        return jsonify({'report': report_html}), 200
        
    except Exception as e:
        logger.error(f"YData report generation failed: {e}")
        return jsonify({'error': str(e)}), 500
