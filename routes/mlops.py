from flask import Blueprint, render_template, session, jsonify, request, current_app
import uuid
import numpy as np
import pandas as pd
import json
import plotly.express as px
import os
import pandas as pd
from datetime import datetime
import math
from core.model_registry import register as register_model_in_registry, list_models as list_models_from_registry
from core.experiment_tracker import log_experiment as log_exp_to_db, list_experiments as list_exp_from_db

#safely import wandb
try:
    import wandb
    _WANDB_AVAILABLE = True
except ImportError:
    _WANDB_AVAILABLE = False


bp = Blueprint('mlops', __name__)

# Use centralized model registry from core.model_registry
experiment_logs = []

@bp.route('/')
def mlops_page():
    return render_template('mlops.html', active_tab='mlops')

@bp.route('/api/models', methods=['GET'])
def list_models():
    """List all registered models"""
    models = list_models_from_registry()
    return jsonify({'models': models})

@bp.route('/api/register', methods=['POST'])
def register_model():
    """Register a trained model"""
    data = request.json
    
    model_id = register_model_in_registry(
        name=data.get('name', f'Model_{len(list_models_from_registry())+1}'),
        model_type=data.get('type', 'unknown'),
        metrics=data.get('metrics', {}),
        hyperparams=data.get('hyperparameters', {}),
        version=data.get('version', '1.0')
    )
    
    # Get the registered model info
    from core.model_registry import get_model
    model_info = get_model(model_id)
    
    return jsonify({'model_id': model_id, 'model': model_info})


@bp.route('/api/log_experiment', methods=['POST'])
def log_experiment():
    """Log a new experiment.

    Body:
      - name: str
      - params: dict
      - metrics: dict
      - status: str
      - tags: list (optional)

    Optional integrations:
      - MLflow: set env MLflow tracking URI via MLFLOW_TRACKING_URI
      - Weights & Biases: set env WANDB_PROJECT
    """
    data = request.json or {}
    
    # Log to SQLite database (persistent)
    exp_id = log_exp_to_db(
        name=data.get('name', f'Experiment_{len(list_exp_from_db())+1}'),
        params=data.get('params', {}),
        metrics=data.get('metrics', {}),
        status=data.get('status', 'completed'),
        tags=data.get('tags', [])
    )
    
    # Get the logged experiment
    experiments = list_exp_from_db(limit=1)
    experiment = experiments[0] if experiments else None
    
    # Also keep in-memory for backward compatibility
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
    # Use persistent SQLite tracker
    experiments = list_exp_from_db()
    return jsonify({'experiments': experiments})

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



@bp.route('/api/detect_drift', methods=['POST'])
def detect_drift_v2():
    """Compare current dataset distribution against a stored baseline."""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400

    data = request.json or {}
    model_id = data.get('model_id')
    baseline = data.get('baseline_stats')  # Pre-stored stats from training time

    if not baseline:
        return jsonify({'error': 'No baseline stats provided'}), 400

    df, _ = current_app.dataset_store.load(dataset_id)
    from scipy import stats

    drift_report = []
    for col, stats_baseline in baseline.items():
        if col not in df.columns:
            continue
        col_data = df[col].dropna()
        if col_data.dtype in ['object', 'category']:
            continue

        # KS test against baseline distribution
        baseline_mean = stats_baseline.get('mean', 0)
        baseline_std = stats_baseline.get('std', 1)
        # Generate baseline sample from stored stats
        baseline_sample = np.random.normal(baseline_mean, baseline_std, 1000)
        ks_stat, p_value = stats.ks_2samp(baseline_sample, col_data.values)

        drift_report.append({
            'column': col,
            'ks_statistic': float(ks_stat),
            'p_value': float(p_value),
            'drift_detected': bool(p_value < 0.05),
            'severity': 'High' if p_value < 0.01 else ('Medium' if p_value < 0.05 else 'None'),
            'current_mean': float(col_data.mean()),
            'baseline_mean': baseline_mean,
            'mean_shift': float(abs(col_data.mean() - baseline_mean))
        })

    drift_report.sort(key=lambda x: x['ks_statistic'], reverse=True)
    return jsonify({
        'drift_report': drift_report,
        'drift_columns': [d['column'] for d in drift_report if d['drift_detected']],
        'overall_drift': any(d['drift_detected'] for d in drift_report)
    })


@bp.route('/api/pipeline_dag', methods=['GET'])
def pipeline_dag():
    """Return a visual DAG of the current processing pipeline."""
    dataset_id = session.get('dataset_id')
    cleaning_log = session.get('cleaning_log', [])

    nodes = [{'id': 'raw_data', 'label': '📁 Raw Data', 'type': 'input'}]
    edges = []
    prev_id = 'raw_data'

    for i, step in enumerate(cleaning_log):
        node_id = f'step_{i}'
        nodes.append({'id': node_id, 'label': step, 'type': 'transform'})
        edges.append({'from': prev_id, 'to': node_id})
        prev_id = node_id

    if prev_id != 'raw_data':
        nodes.append({'id': 'clean_data', 'label': '✅ Cleaned Data', 'type': 'output'})
        edges.append({'from': prev_id, 'to': 'clean_data'})

    return jsonify({'nodes': nodes, 'edges': edges})


@bp.route('/api/experiment-compare', methods=['POST'])
def experiment_compare():
    """Compare multiple experiments with visualization.
    
    Body:
      - experiment_ids: list of experiment IDs to compare
      - metrics: optional list of specific metrics to compare (if not provided, uses common metrics)
      
    Returns comparison data and Plotly chart JSON.
    """
    data = request.json or {}
    exp_ids = data.get('experiment_ids', [])
    
    if len(exp_ids) < 2:
        return jsonify({'error': 'At least two experiment IDs required for comparison'}), 400
    
    # Get all experiments
    all_experiments = list_exp_from_db()
    selected_experiments = [exp for exp in all_experiments if exp['id'] in exp_ids]
    
    if len(selected_experiments) != len(exp_ids):
        found_ids = [exp['id'] for exp in selected_experiments]
        missing = set(exp_ids) - set(found_ids)
        return jsonify({'error': f'Missing experiments: {missing}'}), 400
    
    # Parse metrics from experiments
    experiments_with_metrics = []
    for exp in selected_experiments:
        metrics = json.loads(exp['metrics']) if isinstance(exp['metrics'], str) else exp['metrics']
        params = json.loads(exp['params']) if isinstance(exp['params'], str) else exp['params']
        experiments_with_metrics.append({
            'id': exp['id'],
            'name': exp['name'],
            'metrics': metrics,
            'params': params,
            'timestamp': exp['timestamp']
        })
    
    # Find common metrics across all experiments
    common_metrics = set()
    for i, exp in enumerate(experiments_with_metrics):
        metric_keys = set(exp['metrics'].keys())
        if i == 0:
            common_metrics = metric_keys
        else:
            common_metrics &= metric_keys
    
    if not common_metrics:
        return jsonify({'error': 'No common metrics found across selected experiments'}), 400
    
    # Use user-specified metrics if provided, otherwise use common metrics
    target_metrics = data.get('metrics') or sorted(list(common_metrics))
    
    # Prepare data for comparison chart
    chart_data = []
    for exp in experiments_with_metrics:
        for metric in target_metrics:
            if metric in exp['metrics']:
                try:
                    value = float(exp['metrics'][metric])
                    if not math.isnan(value):
                        chart_data.append({
                            'Experiment': f"{exp['name']} ({exp['id'][:8]})",
                            'Metric': metric,
                            'Value': value
                        })
                except (TypeError, ValueError):
                    continue
    
    if not chart_data:
        return jsonify({'error': 'No valid numeric metrics to display'}), 400
    
    # Create comparison bar chart using Plotly
    df_chart = pd.DataFrame(chart_data)
    fig = px.bar(
        df_chart, 
        x='Experiment', 
        y='Value', 
        color='Metric',
        title='Experiment Metrics Comparison',
        barmode='group',
        text='Value'
    )
    fig.update_traces(texttemplate='%{text:.3g}', textposition='outside')
    fig.update_layout(
        uniformtext_minsize=8, 
        uniformtext_mode='hide',
        xaxis_tickangle=-45,
        height=500
    )
    
    # Convert chart to JSON for frontend rendering
    chart_json = json.loads(fig.to_json())
    
    # Calculate performance differences
    comparisons = []
    baseline_exp = experiments_with_metrics[0]
    for target_exp in experiments_with_metrics[1:]:
        for metric in target_metrics:
            if metric in baseline_exp['metrics'] and metric in target_exp['metrics']:
                try:
                    base_val = float(baseline_exp['metrics'][metric])
                    target_val = float(target_exp['metrics'][metric])
                    if base_val != 0:
                        change_pct = ((target_val - base_val) / abs(base_val)) * 100
                    else:
                        change_pct = float('inf') if target_val > 0 else float('-inf')
                    
                    direction = 'improvement' if change_pct > 0 else 'regression'
                    comparisons.append({
                        'baseline_experiment': {
                            'id': baseline_exp['id'],
                            'name': baseline_exp['name']
                        },
                        'comparison_experiment': {
                            'id': target_exp['id'],
                            'name': target_exp['name']
                        },
                        'metric': metric,
                        'baseline_value': base_val,
                        'comparison_value': target_val,
                        'change_percent': round(change_pct, 2),
                        'direction': direction
                    })
                except (TypeError, ValueError):
                    continue
    
    return jsonify({
        'experiments': experiments_with_metrics,
        'common_metrics': sorted(list(common_metrics)),
        'comparison_chart': chart_json,
        'detailed_comparisons': comparisons,
        'summary': {
            'total_experiments': len(experiments_with_metrics),
            'compared_metrics': len(target_metrics),
            'generated_at': datetime.now().isoformat()
        }
    })

@bp.route('/api/ab_test', methods=['POST'])
def ab_test():
    """Statistical comparison of two registered models."""
    data = request.json or {}
    model_a_id = data.get('model_a')
    model_b_id = data.get('model_b')
    metric = data.get('metric', 'accuracy')

    exps = list_exp_from_db()
    model_a = next((e for e in exps if e['id'] == model_a_id), None)
    model_b = next((e for e in exps if e['id'] == model_b_id), None)

    if not model_a or not model_b:
        return jsonify({'error': 'One or both model experiments not found'}), 404

    metrics_a = json.loads(model_a['metrics']) if isinstance(model_a['metrics'], str) else model_a['metrics']
    metrics_b = json.loads(model_b['metrics']) if isinstance(model_b['metrics'], str) else model_b['metrics']

    score_a = metrics_a.get(metric, 0)
    score_b = metrics_b.get(metric, 0)
    winner = 'A' if score_a > score_b else ('B' if score_b > score_a else 'Tie')
    improvement = abs(score_a - score_b) / max(score_a, score_b, 1e-9) * 100

    return jsonify({
        'model_a': {'id': model_a_id, 'name': model_a['name'], 'score': score_a},
        'model_b': {'id': model_b_id, 'name': model_b['name'], 'score': score_b},
        'metric': metric,
        'winner': winner,
        'improvement_pct': round(improvement, 2)
    })


@bp.route('/api/generate_api', methods=['POST'])
def generate_api():
    """Generate Flask API scaffold for model deployment"""
    data = request.json
    model_id = data.get('model_id')
    
    # Get model info using the get_model function from model_registry
    from core.model_registry import get_model
    model = get_model(model_id)
    
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
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


@bp.route('/api/experiments/session', methods=['GET'])
def get_session_experiments():
    """Get experiments from current session for quick comparison"""
    # Get experiments from database
    experiments = list_exp_from_db(limit=50)
    
    # Parse metrics and params
    parsed_experiments = []
    for exp in experiments:
        try:
            metrics = json.loads(exp['metrics']) if isinstance(exp['metrics'], str) else exp['metrics']
            params = json.loads(exp['params']) if isinstance(exp['params'], str) else exp['params']
            
            # Extract key metrics for display
            key_metrics = {}
            for k in ['accuracy', 'f1', 'r2', 'rmse', 'precision', 'recall']:
                if k in metrics:
                    try:
                        key_metrics[k] = round(float(metrics[k]), 4)
                    except (TypeError, ValueError):
                        pass
            
            parsed_experiments.append({
                'run_id': exp['id'][:8].upper(),
                'timestamp': exp['timestamp'],
                'name': exp['name'],
                'problem_type': params.get('problem_type', 'Unknown'),
                'model': params.get('model', 'Unknown'),
                'n_features': params.get('n_features', 0),
                'metrics': key_metrics,
                'all_metrics': metrics
            })
        except Exception as e:
            continue
    
    return jsonify({'experiments': parsed_experiments})


@bp.route('/api/experiments/clear', methods=['POST'])
def clear_experiments():
    """Clear all experiments from database"""
    from core.experiment_tracker import clear_experiments
    clear_experiments()
    experiment_logs.clear()
    return jsonify({'success': True, 'message': 'All experiments cleared'})
