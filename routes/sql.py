from flask import Blueprint, render_template, session, jsonify, request, current_app
import duckdb

bp = Blueprint('sql', __name__)

@bp.route('/')
def sql_page():
    return render_template('sql.html', active_tab='sql')

@bp.route('/api/execute', methods=['POST'])
def execute():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, _ = current_app.dataset_store.load(dataset_id)
    query = request.json.get('query', '')
    try:
        con = duckdb.connect()
        con.register('df', df)
        result_df = con.execute(query).fetchdf()
        con.close()
        return jsonify({
            'columns': list(result_df.columns),
            'rows': result_df.to_dict(orient='records'),
            'shape': result_df.shape
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
