from flask import Blueprint, render_template, session, jsonify, request, current_app
import pandas as pd

bp = Blueprint('cleaning', __name__)

@bp.route('/')
def cleaning_page():
    return render_template('cleaning.html', active_tab='cleaning')

@bp.route('/api/analyze', methods=['GET'])
def analyze():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, _ = current_app.dataset_store.load(dataset_id)
    issues = []
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().head(100)
            try:
                pd.to_numeric(sample, errors='raise')
                issues.append({'column': col, 'issue': 'Contains numeric characters but stored as text',
                    'recommendation': "Convert to numeric using pd.to_numeric(..., errors='coerce')", 'severity': 'Medium'})
            except: pass
            try:
                pd.to_datetime(sample, errors='raise')
                issues.append({'column': col, 'issue': 'Looks like a date but stored as text',
                    'recommendation': 'Convert to datetime using pd.to_datetime()', 'severity': 'Medium'})
            except: pass
    return jsonify({'issues': issues, 'issue_count': len(issues)})

@bp.route('/api/apply', methods=['POST'])
def apply_fixes():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, name = current_app.dataset_store.load(dataset_id)
    fixes = request.json.get('fixes', [])
    log = []
    for fix in fixes:
        col, action = fix['column'], fix['action']
        if action == 'to_numeric':
            df[col] = pd.to_numeric(df[col], errors='coerce'); log.append(f"Converted {col} to numeric")
        elif action == 'to_datetime':
            df[col] = pd.to_datetime(df[col], errors='coerce'); log.append(f"Converted {col} to datetime")
        elif action == 'drop_na':
            before = len(df); df = df.dropna(subset=[col]); log.append(f"Dropped {before - len(df)} NA rows from {col}")
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    session['cleaning_log'] = session.get('cleaning_log', []) + log
    return jsonify({'new_dataset_id': new_id, 'shape': df.shape, 'log': log,
        'preview': df.head(5).to_dict(orient='records')})
