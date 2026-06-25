from flask import Blueprint, render_template, session, jsonify, current_app

bp = Blueprint('review', __name__)

@bp.route('/')
def review_page():
    return render_template('review.html', active_tab='review')

@bp.route('/api/profile', methods=['GET'])
def profile():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, name = current_app.dataset_store.load(dataset_id)
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    memory_kb = df.memory_usage(deep=True).sum() / 1024
    return jsonify({
        'name': name,
        'rows': len(df),
        'columns': len(df.columns),
        'nulls': int(df.isnull().sum().sum()),
        'duplicates': int(df.duplicated().sum()),
        'memory_kb': round(memory_kb, 1),
        'dtypes': {c: str(t) for c, t in df.dtypes.items()},
        'numeric_summary': df[numeric_cols].describe().to_dict() if numeric_cols else {},
        'top_rows': df.head(10).to_dict(orient='records'),
        'bottom_rows': df.tail(10).to_dict(orient='records'),
    })
