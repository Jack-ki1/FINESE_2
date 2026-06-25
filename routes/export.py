import os
from flask import Blueprint, render_template, session, send_file, jsonify, current_app
import io
import pandas as pd

bp = Blueprint('export', __name__)

@bp.route('/')
def export_page():
    return render_template('export.html', active_tab='export')

@bp.route('/api/download/<format>', methods=['GET'])
def download(format):
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, name = current_app.dataset_store.load(dataset_id)
    base = os.path.splitext(name)[0] if name else 'data'
    buf = io.BytesIO()
    if format == 'csv':
        df.to_csv(buf, index=False); buf.seek(0)
        return send_file(buf, mimetype='text/csv', download_name=f'{base}.csv', as_attachment=True)
    elif format == 'excel':
        df.to_excel(buf, index=False); buf.seek(0)
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name=f'{base}.xlsx', as_attachment=True)
    elif format == 'json':
        df.to_json(buf, orient='records'); buf.seek(0)
        return send_file(buf, mimetype='application/json', download_name=f'{base}.json', as_attachment=True)
    return jsonify({'error': 'Unsupported format'}), 400
