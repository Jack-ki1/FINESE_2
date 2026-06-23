"""
FINESE2 - AI Assistant API Routes
Handles AI chat and data analysis requests.
"""
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import json
from app.services.data_service import data_service
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

ai_bp = Blueprint('api_ai', __name__)


@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """Send message to AI assistant."""
    try:
        user_id = get_jwt_identity()
        messages = request.json.get('messages', [])
        provider = request.json.get('provider', 'openai')
        model = request.json.get('model')
        dataset_context = request.json.get('dataset_context')
        
        if not messages:
            return jsonify({'error': 'Messages required'}), 400
        
        result = ai_service.chat(
            messages=messages,
            user_id=user_id,
            dataset_context=dataset_context,
            provider=provider,
            model=model
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/chat/stream', methods=['POST'])
@jwt_required()
def stream_chat():
    """Stream chat responses from AI assistant."""
    try:
        user_id = get_jwt_identity()
        messages = request.json.get('messages', [])
        provider = request.json.get('provider', 'openai')
        model = request.json.get('model')
        
        if not messages:
            return jsonify({'error': 'Messages required'}), 400
        
        def generate():
            for chunk in ai_service.stream_chat(
                messages=messages,
                user_id=user_id,
                provider=provider,
                model=model
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
        
    except Exception as e:
        logger.error(f"AI streaming chat failed: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/analyze-data', methods=['POST'])
@jwt_required()
def analyze_data():
    """Get AI analysis of dataset."""
    try:
        user_id = get_jwt_identity()
        dataset_id = request.json.get('dataset_id')
        user_query = request.json.get('query', 'Analyze this dataset')
        provider = request.json.get('provider', 'openai')
        
        if not dataset_id:
            return jsonify({'error': 'Dataset ID required'}), 400
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return jsonify({'error': 'Dataset not found or access denied'}), 404
        
        # Create dataset summary
        df_summary = {
            'shape': list(df.shape),
            'columns': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing': {col: int(df[col].isnull().sum()) for col in df.columns},
            'numeric_summary': {}
        }
        
        # Add numeric summaries
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            df_summary['numeric_summary'][col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max())
            }
        
        result = ai_service.analyze_data_with_ai(
            df_summary=df_summary,
            user_query=user_query,
            user_id=user_id,
            provider=provider
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"AI data analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/providers', methods=['GET'])
@jwt_required()
def get_providers():
    """Get available AI providers."""
    providers = ai_service.get_available_providers()
    return jsonify({'providers': providers}), 200
