import os
from flask import Blueprint, request, jsonify, session, current_app
import pandas as pd

bp = Blueprint('data', __name__, url_prefix='/api/data')
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json'}

@bp.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Unsupported format: {ext}'}), 400

    try:
        if ext == '.csv':
            df = pd.read_csv(file)
        elif ext in ('.xlsx', '.xls'):
            df = pd.read_excel(file)
        elif ext == '.json':
            df = pd.read_json(file)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    store = current_app.dataset_store
    old_id = session.get('dataset_id')
    if old_id:
        store.delete(old_id)

    dataset_id = store.save(df, file.filename)
    session['dataset_id'] = dataset_id
    session['dataset_name'] = file.filename
    session['cleaning_log'] = []
    
    # Update global dataset tracker for context processor
    from core.dataset_store import set_current_dataset
    set_current_dataset(dataset_id, file.filename, df.shape)

    return jsonify({
        'dataset_id': dataset_id,
        'name': file.filename,
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': {k: str(v) for k, v in df.dtypes.items()}
    })

@bp.route('/info', methods=['GET'])
def info():
    dataset_id = session.get('dataset_id')
    if not dataset_id or not current_app.dataset_store.exists(dataset_id):
        # Clear the global tracker if dataset doesn't exist
        from core.dataset_store import clear_current_dataset
        clear_current_dataset()
        return jsonify({'loaded': False})
    
    df, name = current_app.dataset_store.load(dataset_id)
    
    # Update global tracker with current dataset info
    from core.dataset_store import set_current_dataset
    set_current_dataset(dataset_id, name, df.shape)
    
    return jsonify({
        'loaded': True,
        'name': name,
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': {k: str(v) for k, v in df.dtypes.items()}
    })
