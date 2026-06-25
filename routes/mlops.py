from flask import Blueprint, render_template, session, jsonify, request, current_app
import uuid
import json
import os
from datetime import datetime

bp = Blueprint('mlops', __name__)

# In-memory model registry (in production, use database)
model_registry = {}
experiment_logs = []

@bp.route('/')
def mlops_page():
    return render_template('mlops.html', active_tab='mlops')

@bp.route('/api/models', methods=['GET'])
def list_models():
    """List all registered models"""
    return jsonify({'models': list(model_registry.values())})

@bp.route('/api/register', methods=['POST'])
def register_model():
    """Register a trained model"""
    data = request.json
    model_id = str(uuid.uuid4())
    
    model_info = {
        'id': model_id,
        'name': data.get('name', f'Model_{len(model_registry)+1}'),
        'type': data.get('type', 'unknown'),
        'metrics': data.get('metrics', {}),
        'hyperparameters': data.get('hyperparameters', {}),
        'created_at': datetime.now().isoformat(),
        'status': 'registered',
        'version': data.get('version', '1.0')
    }
    
    model_registry[model_id] = model_info
    return jsonify({'model_id': model_id, 'model': model_info})

@bp.route('/api/experiments', methods=['GET'])
def list_experiments():
    """List all experiments"""
    return jsonify({'experiments': experiment_logs})

@bp.route('/api/log_experiment', methods=['POST'])
def log_experiment():
    """Log a new experiment"""
    data = request.json
    exp_id = str(uuid.uuid4())
    
    experiment = {
        'id': exp_id,
        'name': data.get('name', f'Experiment_{len(experiment_logs)+1}'),
        'params': data.get('params', {}),
        'metrics': data.get('metrics', {}),
        'status': data.get('status', 'completed'),
        'timestamp': datetime.now().isoformat()
    }
    
    experiment_logs.append(experiment)
    return jsonify({'experiment_id': exp_id, 'experiment': experiment})

@bp.route('/api/drift检测', methods=['POST'])
def detect_drift():
    """Detect data drift between training and current data"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    
    # Simple drift detection using statistical tests
    drift_report = {
        'overall_drift': False,
        'column_drifts': {},
        'recommendations': []
    }
    
    # Check for distribution changes in numeric columns
    numeric_cols = df.select_dtypes(include='number').columns
    for col in numeric_cols:
        mean_val = df[col].mean()
        std_val = df[col].std()
        
        # Simple heuristic: flag if std is very high relative to mean
        if std_val > abs(mean_val) * 2:
            drift_report['column_drifts'][col] = {
                'drift_detected': True,
                'mean': float(mean_val),
                'std': float(std_val),
                'severity': 'high' if std_val > abs(mean_val) * 3 else 'medium'
            }
            drift_report['overall_drift'] = True
    
    if drift_report['overall_drift']:
        drift_report['recommendations'].append(
            "Data drift detected. Consider retraining your model with recent data."
        )
    
    return jsonify(drift_report)

@bp.route('/api/generate_api', methods=['POST'])
def generate_api():
    """Generate Flask API scaffold for model deployment"""
    data = request.json
    model_id = data.get('model_id')
    
    if not model_id or model_id not in model_registry:
        return jsonify({'error': 'Model not found'}), 404
    
    model = model_registry[model_id]
    
    api_code = f"""
from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)
model = joblib.load('models/{model['name']}.pkl')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    df = pd.DataFrame([data])
    prediction = model.predict(df)
    return jsonify({{'prediction': prediction.tolist()}})

if __name__ == '__main__':
    app.run(port=5001)
"""
    
    return jsonify({'api_code': api_code, 'model_name': model['name']})
