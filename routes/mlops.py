from flask import Blueprint, render_template, session, jsonify, request, current_app
import uuid
import numpy as np
import pandas as pd
import json
import plotly.express as px
import wandb
import os
import pandas as pd
from datetime import datetime
import math


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


@bp.route('/api/log_experiment', methods=['POST'])
def log_experiment():

    """Log a new experiment.

    Body:
      - name: str
      - params: dict
      - metrics: dict
      - status: str

    Optional integrations:
      - MLflow: set env MLflow tracking URI via MLFLOW_TRACKING_URI
      - Weights & Biases: set env WANDB_PROJECT
    """
    data = request.json or {}
    exp_id = str(uuid.uuid4())

    experiment = {
        'id': exp_id,
        'name': data.get('name', f'Experiment_{len(experiment_logs)+1}'),
        'params': data.get('params', {}),
        'metrics': data.get('metrics', {}),
        'status': data.get('status', 'completed'),
        'timestamp': datetime.now().isoformat()
    }

    # Always store in-memory
    experiment_logs.append(experiment)

    # Optional MLflow/W&B logging (best-effort)
    try:
        tracking_uri = os.getenv('MLFLOW_TRACKING_URI', '').strip()
        if tracking_uri:
            import mlflow
            mlflow.set_tracking_uri(tracking_uri)

        if tracking_uri or os.getenv('ENABLE_MLFLOW', '').lower() in ['1', 'true', 'yes']:
            import mlflow
            with mlflow.start_run(run_name=experiment['name']):
                for k, v in (experiment['params'] or {}).items():
                    mlflow.log_param(k, v)
                for k, v in (experiment['metrics'] or {}).items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        mlflow.log_metric(k, float(v))
    except Exception:
        # ignore integration errors
        pass

    try:
        if os.getenv('WANDB_PROJECT'):
            import wandb
            wandb.init(project=os.getenv('WANDB_PROJECT'), name=experiment['name'], reinit=True)
            for k, v in (experiment['params'] or {}).items():
                wandb.config[k] = v
            for k, v in (experiment['metrics'] or {}).items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    wandb.log({k: float(v)})
            wandb.finish()
    except Exception:
        pass

    return jsonify({'experiment_id': exp_id, 'experiment': experiment})

@bp.route('/api/experiments', methods=['GET'])
def list_experiments():
    """List all experiments"""
    return jsonify({'experiments': experiment_logs})

@bp.route('/api/feature-store/register', methods=['POST'])
def feature_store_register():
    """Register a feature transformation (metadata only).

    Body:
      - name: str
      - type: str (e.g., numeric, categorical)
      - description: str
      - transformation: str (limited to known safe operations)
    """
    if not hasattr(bp, 'feature_store'):
        bp.feature_store = {}

    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Feature name required'}), 400

    if data.get('transformation') not in [None, '', 'identity', 'log1p', 'sqrt', 'zscore', 'minmax']:
        return jsonify({'error': 'Unsupported transformation (safe list only)'}), 400

    bp.feature_store[name] = {
        'name': name,
        'type': data.get('type', 'numeric'),
        'description': data.get('description', ''),
        'transformation': data.get('transformation', 'identity'),
        'created_at': datetime.now().isoformat(),
        'usage_count': 0
    }

    return jsonify({'success': True, 'feature': bp.feature_store[name]})

@bp.route('/api/feature-store/compute', methods=['POST'])
def feature_store_compute():
    """Compute registered safe feature transformations on current dataset.

    Body:
      - features: [feature_name1, ...]
    """
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400

    if not hasattr(bp, 'feature_store') or not bp.feature_store:
        return jsonify({'error': 'No features registered'}), 400

    df, _ = current_app.dataset_store.load(dataset_id)
    data = request.json or {}
    feature_names = data.get('features', [])

    if not feature_names:
        return jsonify({'error': 'No features requested'}), 400

    out = {}
    for fname in feature_names:
        if fname not in bp.feature_store:
            continue
        meta = bp.feature_store[fname]
        # We expect fname itself maps to a column in df
        if fname not in df.columns:
            continue

        s = df[fname]
        tf = meta.get('transformation', 'identity')
        try:
            if tf == 'identity':
                out[fname] = s
            elif tf == 'log1p':
                out[fname] = np.log1p(s.astype(float).abs())
            elif tf == 'sqrt':
                out[fname] = np.sqrt(s.astype(float).abs())
            elif tf == 'zscore':
                ss = s.astype(float)
                out[fname] = (ss - ss.mean()) / (ss.std() if ss.std() != 0 else 1)
            elif tf == 'minmax':
                ss = s.astype(float)
                denom = (ss.max() - ss.min())
                out[fname] = (ss - ss.min()) / (denom if denom != 0 else 1)
            bp.feature_store[fname]['usage_count'] = int(bp.feature_store[fname].get('usage_count', 0)) + 1
        except Exception:
            out[fname] = None

    return jsonify({'features': {k: (v.fillna(np.nan).tolist()[:1000] if v is not None else None) for k, v in out.items()}, 'note': 'Returned first 1000 values per feature for payload size'})

@bp.route('/api/drift检测', methods=['POST'])
def detect_drift():
    """Detect data drift between (optional) baseline and current data.

    Body (optional JSON):
      - baseline_stats: {"columns": {col: {"sample": [...]} }} or {"columns": {col: {"values": [...]}}]
        If not provided, falls back to distribution-stat heuristic and KS test where possible.

    """

    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400

    df, _ = current_app.dataset_store.load(dataset_id)
    body = request.json or {}
    baseline_stats = body.get('baseline_stats')

    drift_report = {
        'overall_drift': False,
        'column_drifts': {},
        'recommendations': []
    }

    numeric_cols = df.select_dtypes(include='number').columns.tolist()

    # Try KS-test when baseline samples are provided
    if isinstance(baseline_stats, dict):
        baseline_cols = baseline_stats.get('columns', {}) or baseline_stats.get('cols', {})
        from scipy.stats import ks_2samp

        for col in numeric_cols:
            current_series = df[col].dropna().astype(float)
            if current_series.shape[0] < 30:
                continue

            base_obj = baseline_cols.get(col, {})
            base_values = base_obj.get('sample') or base_obj.get('values')

            if not isinstance(base_values, list) or len(base_values) < 30:
                continue

            base_arr = pd.Series(base_values).dropna().astype(float)
            if base_arr.shape[0] < 30:
                continue

            # subsample for speed
            if len(base_arr) > 2000:
                base_arr = base_arr.sample(2000, random_state=42)
            if len(current_series) > 2000:
                current_series = current_series.sample(2000, random_state=42)

            res = ks_2samp(base_arr.values, current_series.values, alternative='two-sided', mode='auto')
            # res.pvalue small => drift
            if res.pvalue <= 0.05:
                drift_report['column_drifts'][col] = {
                    'drift_detected': True,
                    'test': 'ks_2samp',
                    'ks_statistic': float(res.statistic),
                    'p_value': float(res.pvalue),
                    'current_mean': float(current_series.mean()),
                    'baseline_mean': float(base_arr.mean()),
                }
                drift_report['overall_drift'] = True

    # Fallback heuristic when baseline not provided or KS didn't flag
    if not drift_report['overall_drift']:
        for col in numeric_cols:
            mean_val = df[col].mean()
            std_val = df[col].std()
            if pd.isna(mean_val) or pd.isna(std_val):
                continue

            # Simple heuristic: std very high relative to mean
            if std_val > abs(mean_val) * 2:
                drift_report['column_drifts'][col] = {
                    'drift_detected': True,
                    'test': 'mean/std heuristic',
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
