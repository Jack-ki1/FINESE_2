"""
FINESE2 - Consolidated Visualization API Routes
Handles all visualization operations using the consolidated visualization module.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.core.visualize import visualizer
from app.core.data import data_manager

logger = logging.getLogger(__name__)

visualization_bp = Blueprint('api_visualization', __name__)


@visualization_bp.route('/create', methods=['POST'])
@jwt_required()
def create_chart():
    """Create a visualization chart."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        chart_type = request.json.get('chart_type')
        x_col = request.json.get('x_col')
        y_col = request.json.get('y_col')
        color_col = request.json.get('color_col')
        
        if not all([dataset_id, chart_type, x_col]):
            return jsonify({'error': 'Dataset ID, chart type, and x column required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Create chart based on type
        if chart_type == 'scatter':
            fig = visualizer.create_scatter_plot(df, x_col, y_col, color_col)
        elif chart_type == 'line':
            fig = visualizer.create_line_plot(df, x_col, y_col, color_col)
        elif chart_type == 'bar':
            fig = visualizer.create_bar_plot(df, x_col, y_col, color_col)
        elif chart_type == 'histogram':
            fig = visualizer.create_histogram(df, x_col, color_col)
        elif chart_type == 'box':
            fig = visualizer.create_box_plot(df, y_col, x_col, color_col)
        elif chart_type == 'heatmap':
            columns = request.json.get('columns', None)
            fig = visualizer.create_heatmap(df, columns)
        elif chart_type == 'pie':
            values_col = request.json.get('values_col')
            names_col = request.json.get('names_col')
            fig = visualizer.create_pie_chart(df, values_col, names_col)
        elif chart_type == 'violin':
            fig = visualizer.create_violin_plot(df, y_col, x_col, color_col)
        else:
            return jsonify({'error': f'Unsupported chart type: {chart_type}'}), 400
        
        # Convert figure to JSON for transmission
        chart_json = fig.to_json()
        
        return jsonify({
            'chart_type': chart_type,
            'chart_data': chart_json
        }), 200
        
    except Exception as e:
        logger.error(f"Creating chart failed: {e}")
        return jsonify({'error': str(e)}), 500


@visualization_bp.route('/types', methods=['GET'])
@jwt_required()
def get_chart_types():
    """Get available chart types."""
    try:
        chart_types = [
            {'type': 'scatter', 'description': 'Scatter plot'},
            {'type': 'line', 'description': 'Line chart'},
            {'type': 'bar', 'description': 'Bar chart'},
            {'type': 'histogram', 'description': 'Histogram'},
            {'type': 'box', 'description': 'Box plot'},
            {'type': 'heatmap', 'description': 'Heatmap'},
            {'type': 'pie', 'description': 'Pie chart'},
            {'type': 'violin', 'description': 'Violin plot'},
            {'type': 'time_series', 'description': 'Time series'},
            {'type': 'pair', 'description': 'Pair plot'},
            {'type': 'radar', 'description': 'Radar chart'}
        ]
        
        return jsonify({'chart_types': chart_types}), 200
        
    except Exception as e:
        logger.error(f"Getting chart types failed: {e}")
        return jsonify({'error': str(e)}), 500


@visualization_bp.route('/time-series', methods=['POST'])
@jwt_required()
def create_time_series():
    """Create a time series visualization."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        date_col = request.json.get('date_col')
        value_col = request.json.get('value_col')
        color_col = request.json.get('color_col')
        
        if not all([dataset_id, date_col, value_col]):
            return jsonify({'error': 'Dataset ID, date column, and value column required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        fig = visualizer.create_time_series(df, date_col, value_col, color_col)
        chart_json = fig.to_json()
        
        return jsonify({
            'chart_type': 'time_series',
            'chart_data': chart_json
        }), 200
        
    except Exception as e:
        logger.error(f"Creating time series failed: {e}")
        return jsonify({'error': str(e)}), 500


@visualization_bp.route('/correlation-matrix', methods=['POST'])
@jwt_required()
def create_correlation_matrix():
    """Create a correlation matrix visualization."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        columns = request.json.get('columns', None)
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_manager.get_dataset(dataset_id)
        if df is None:
            return jsonify({'error': 'Dataset not found'}), 404
        
        fig = visualizer.create_heatmap(df, columns)
        chart_json = fig.to_json()
        
        return jsonify({
            'chart_type': 'correlation_matrix',
            'chart_data': chart_json
        }), 200
        
    except Exception as e:
        logger.error(f"Creating correlation matrix failed: {e}")
        return jsonify({'error': str(e)}), 500