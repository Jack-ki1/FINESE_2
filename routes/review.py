from flask import Blueprint, render_template, session, jsonify, current_app
import pandas as pd
import numpy as np
from scipy import stats

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

@bp.route('/api/statistics/normality', methods=['GET'])
def normality_test():
    """Shapiro-Wilk normality test for all numeric columns"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    results = []
    for col in numeric_cols:
        # Drop NaN values for the test
        clean_data = df[col].dropna()
        
        if len(clean_data) < 3 or len(clean_data) > 5000:
            # Shapiro-Wilk requires 3-5000 samples
            continue
        
        stat, p_value = stats.shapiro(clean_data)
        results.append({
            'column': col,
            'statistic': float(stat),
            'p_value': float(p_value)
        })
    
    return jsonify({'results': results})

@bp.route('/api/statistics/correlation', methods=['GET'])
def correlation_analysis():

    """Generate correlation matrix heatmap"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.shape[1] < 2:
        return jsonify({'error': 'Need at least 2 numeric columns'}), 400
    
    corr_matrix = numeric_df.corr()
    
    import plotly.graph_objects as go
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmin=-1,
        zmax=1,
        text=np.round(corr_matrix.values, 2),
        hovertemplate='%{x} vs %{y}<br>Correlation: %{text}<extra></extra>',
        texttemplate='%{text:.2f}'
    ))
    
    fig.update_layout(
        title='Correlation Matrix Heatmap',
        xaxis_title='Features',
        yaxis_title='Features',
        template='plotly_white',
        height=600,
        width=800
    )
    
    import json
    import plotly.utils
    return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})

@bp.route('/api/statistics/hypothesis', methods=['POST'])
def hypothesis_test():
    """Perform hypothesis tests (t-test, ANOVA, chi-square)"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    test_type = request.json.get('test_type', '1')
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if test_type == '1':
        # T-test: Compare first two numeric columns
        if len(numeric_cols) < 2:
            return jsonify({'error': 'Need at least 2 numeric columns for t-test'}), 400
        
        col1, col2 = numeric_cols[0], numeric_cols[1]
        stat, p_value = stats.ttest_ind(df[col1].dropna(), df[col2].dropna())
        
        return jsonify({
            'test_name': 'Independent T-Test',
            'columns': [col1, col2],
            'statistic': float(stat),
            'p_value': float(p_value)
        })
    
    elif test_type == '2':
        # ANOVA: Compare first 3 numeric columns
        if len(numeric_cols) < 3:
            return jsonify({'error': 'Need at least 3 numeric columns for ANOVA'}), 400
        
        groups = [df[col].dropna() for col in numeric_cols[:3]]
        stat, p_value = stats.f_oneway(*groups)
        
        return jsonify({
            'test_name': 'One-Way ANOVA',
            'columns': numeric_cols[:3],
            'statistic': float(stat),
            'p_value': float(p_value)
        })
    
    elif test_type == '3':
        # Chi-square: Compare first 2 categorical columns
        if len(categorical_cols) < 2:
            return jsonify({'error': 'Need at least 2 categorical columns for chi-square'}), 400
        
        col1, col2 = categorical_cols[0], categorical_cols[1]
        contingency = pd.crosstab(df[col1], df[col2])
        stat, p_value, dof, expected = stats.chi2_contingency(contingency)
        
        return jsonify({
            'test_name': 'Chi-Square Test',
            'columns': [col1, col2],
            'statistic': float(stat),
            'p_value': float(p_value)
        })
    
    return jsonify({'error': 'Invalid test type'}), 400

@bp.route('/api/statistics/summary', methods=['GET'])
def statistical_summary():
    """Generate comprehensive statistical summary"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    summary = []
    for col in numeric_cols:
        data = df[col].dropna()
        if len(data) == 0:
            continue
        
        summary.append({
            'column': col,
            'mean': float(data.mean()),
            'median': float(data.median()),
            'std': float(data.std()),
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data)),
            'min': float(data.min()),
            'max': float(data.max()),
            'q1': float(data.quantile(0.25)),
            'q3': float(data.quantile(0.75))
        })
    
    return jsonify({'summary': summary})
