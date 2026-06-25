from flask import Blueprint, render_template, session, jsonify, request, current_app
import plotly.express as px
import plotly.utils
import json

bp = Blueprint('charts', __name__)

@bp.route('/')
def charts_page():
    return render_template('charts.html', active_tab='charts')

@bp.route('/api/build', methods=['POST'])
def build_chart():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, _ = current_app.dataset_store.load(dataset_id)
    cfg = request.json
    chart_type, x, y, color = cfg.get('type', 'bar'), cfg.get('x'), cfg.get('y'), cfg.get('color')
    try:
        if chart_type == 'bar': fig = px.bar(df, x=x, y=y, color=color)
        elif chart_type == 'line': fig = px.line(df, x=x, y=y, color=color)
        elif chart_type == 'scatter': fig = px.scatter(df, x=x, y=y, color=color)
        elif chart_type == 'histogram': fig = px.histogram(df, x=x, color=color)
        elif chart_type == 'box': fig = px.box(df, x=x, y=y, color=color)
        else: fig = px.bar(df, x=x, y=y)
        fig.update_layout(template='plotly_white', margin=dict(l=20, r=20, t=40, b=20))
        return jsonify({'graph_json': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
