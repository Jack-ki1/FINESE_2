from flask import Blueprint, render_template, session, jsonify, current_app, request
import pandas as pd
import numpy as np
from scipy import stats
from cachetools import TTLCache
import hashlib

bp = Blueprint('review', __name__)

# Cache for profile data (5 minute TTL)
_profile_cache = TTLCache(maxsize=20, ttl=300)

@bp.route('/')
def review_page():
    return render_template('review.html', active_tab='review')

@bp.route('/api/profile', methods=['GET'])
def profile():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    # Check cache first
    cache_key = dataset_id
    if cache_key in _profile_cache:
        return jsonify(_profile_cache[cache_key])
    
    df, name = current_app.dataset_store.load(dataset_id)
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    memory_kb = df.memory_usage(deep=True).sum() / 1024
    
    result = {
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
    }
    
    # Store in cache
    _profile_cache[cache_key] = result
    
    return jsonify(result)

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
        clean_data = df[col].dropna()
        if len(clean_data) < 3:
            continue

        if len(clean_data) <= 5000:
            stat, p_value = stats.shapiro(clean_data)
            test_used = 'Shapiro-Wilk'
        elif len(clean_data) <= 20000:
            stat, p_value = stats.normaltest(clean_data)   # D'Agostino-Pearson
            test_used = "D'Agostino-Pearson"
        else:
            stat, p_value = stats.kstest(clean_data, 'norm',
                                        args=(clean_data.mean(), clean_data.std()))
            test_used = 'Kolmogorov-Smirnov'

        results.append({
            'column': col,
            'test': test_used,
            'statistic': float(stat),
            'p_value': float(p_value),
            'is_normal': bool(p_value > 0.05)
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
    """Perform hypothesis tests (t-test, ANOVA, chi-square) with user-selected columns"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    data = request.json
    test_type = data.get('test_type', '1')
    col1_name = data.get('col1')       # User-supplied column 1
    col2_name = data.get('col2')       # User-supplied column 2
    group_col = data.get('group_col')  # For ANOVA grouping
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if test_type == '1':
        # T-test: Compare two numeric columns
        if not col1_name or not col2_name:
            # Fallback to first two numeric columns if not specified
            if len(numeric_cols) < 2:
                return jsonify({'error': 'Need at least 2 numeric columns for t-test'}), 400
            col1_name, col2_name = numeric_cols[0], numeric_cols[1]
        
        if col1_name not in numeric_cols or col2_name not in numeric_cols:
            return jsonify({'error': 'Both columns must be numeric for t-test'}), 400
        
        stat, p_value = stats.ttest_ind(df[col1_name].dropna(), df[col2_name].dropna())
        
        return jsonify({
            'test_name': 'Independent T-Test',
            'columns': [col1_name, col2_name],
            'statistic': float(stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05)
        })
    
    elif test_type == '2':
        # ANOVA: Compare multiple numeric columns or groups
        if group_col and group_col in categorical_cols:
            # One-way ANOVA with grouping
            if len(numeric_cols) < 1:
                return jsonify({'error': 'Need at least 1 numeric column for ANOVA'}), 400
            
            target_col = col1_name if col1_name and col1_name in numeric_cols else numeric_cols[0]
            groups = [df[target_col][df[group_col] == cat].dropna() 
                     for cat in df[group_col].unique()]
            groups = [g for g in groups if len(g) > 0]
            
            if len(groups) < 2:
                return jsonify({'error': 'Need at least 2 groups for ANOVA'}), 400
            
            stat, p_value = stats.f_oneway(*groups)
            
            return jsonify({
                'test_name': 'One-Way ANOVA',
                'target_column': target_col,
                'group_column': group_col,
                'groups': len(groups),
                'statistic': float(stat),
                'p_value': float(p_value),
                'significant': bool(p_value < 0.05)
            })
        else:
            # Fallback: Compare first 3 numeric columns
            if len(numeric_cols) < 3:
                return jsonify({'error': 'Need at least 3 numeric columns for ANOVA'}), 400
            
            groups = [df[col].dropna() for col in numeric_cols[:3]]
            stat, p_value = stats.f_oneway(*groups)
            
            return jsonify({
                'test_name': 'One-Way ANOVA',
                'columns': numeric_cols[:3],
                'statistic': float(stat),
                'p_value': float(p_value),
                'significant': bool(p_value < 0.05)
            })
    
    elif test_type == '3':
        # Chi-square: Compare two categorical columns
        if not col1_name or not col2_name:
            # Fallback to first two categorical columns
            if len(categorical_cols) < 2:
                return jsonify({'error': 'Need at least 2 categorical columns for chi-square'}), 400
            col1_name, col2_name = categorical_cols[0], categorical_cols[1]
        
        if col1_name not in categorical_cols or col2_name not in categorical_cols:
            return jsonify({'error': 'Both columns must be categorical for chi-square'}), 400
        
        contingency = pd.crosstab(df[col1_name], df[col2_name])
        stat, p_value, dof, expected = stats.chi2_contingency(contingency)
        
        return jsonify({
            'test_name': 'Chi-Square Test',
            'columns': [col1_name, col2_name],
            'statistic': float(stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05)
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

@bp.route('/api/datetime_analysis', methods=['GET'])
def datetime_analysis():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, _ = current_app.dataset_store.load(dataset_id)

    dt_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    results = []

    for col in dt_cols:
        s = df[col].dropna().sort_values()
        gaps = s.diff().dt.days.dropna()
        results.append({
            'column': col,
            'min': str(s.min()),
            'max': str(s.max()),
            'range_days': int((s.max() - s.min()).days),
            'null_count': int(df[col].isna().sum()),
            'avg_gap_days': float(gaps.mean()) if len(gaps) else None,
            'max_gap_days': float(gaps.max()) if len(gaps) else None,
        })

    return jsonify({'datetime_columns': results})

@bp.route('/api/value_counts', methods=['GET'])
def value_counts():
    dataset_id = session.get('dataset_id')
    col = request.args.get('column')
    top_n = int(request.args.get('top_n', 20))
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400

    df, _ = current_app.dataset_store.load(dataset_id)
    if col not in df.columns:
        return jsonify({'error': 'Column not found'}), 400

    vc = df[col].value_counts(dropna=False).head(top_n)
    pct = (vc / len(df) * 100).round(2)

    return jsonify({
        'column': col,
        'cardinality': int(df[col].nunique()),
        'top_values': [
            {'value': str(v), 'count': int(c), 'pct': float(p)}
            for v, c, p in zip(vc.index, vc.values, pct.values)
        ]
    })


@bp.route('/api/null_map', methods=['GET'])
def null_map():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, _ = current_app.dataset_store.load(dataset_id)

    # Sample to max 500 rows for rendering
    sample = df.isnull().astype(int)
    if len(sample) > 500:
        sample = sample.sample(500, random_state=42).reset_index(drop=True)

    import plotly.graph_objects as go, json, plotly.utils
    fig = go.Figure(data=go.Heatmap(
        z=sample.values.T.tolist(),
        x=[str(i) for i in sample.index],
        y=sample.columns.tolist(),
        colorscale=[[0, '#1e293b'], [1, '#ef4444']],
        showscale=False,
        hovertemplate='Row %{x}<br>%{y}: %{z}<extra></extra>'
    ))
    fig.update_layout(
        title='Missing Value Map (red = null)',
        height=max(200, len(df.columns) * 25),
        template='plotly_white',
        xaxis_title='Row index (sample)',
        yaxis_title='Column'
    )
    return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})

@bp.route('/api/vif', methods=['GET'])
def vif_analysis():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, _ = current_app.dataset_store.load(dataset_id)

    from statsmodels.stats.outliers_influence import variance_inflation_factor
    numeric_df = df.select_dtypes(include=[np.number]).dropna()

    if numeric_df.shape[1] < 2:
        return jsonify({'error': 'Need at least 2 numeric columns'}), 400

    vif_data = []
    cols = numeric_df.columns.tolist()
    X = numeric_df.values
    for i, col in enumerate(cols):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data.append({
                'column': col,
                'vif': round(float(vif), 3),
                'risk': 'High' if vif > 10 else ('Medium' if vif > 5 else 'Low')
            })
        except Exception:
            pass

    return jsonify({'vif': sorted(vif_data, key=lambda x: x['vif'], reverse=True)})

"""
@bp.route('/api/statistics/hypothesis', methods=['POST'])
def hypothesis_test():
    ...
    data = request.json
    test_type = data.get('test_type', '1')
    col1_name = data.get('col1')       # ← NEW: user-supplied
    col2_name = data.get('col2')       # ← NEW: user-supplied
    group_col = data.get('group_col')  # ← NEW: for ANOVA grouping

    if test_type == '1':
        if not col1_name or not col2_name:
            return jsonify({'error': 'col1 and col2 required for t-test'}), 400
        stat, p_value = stats.ttest_ind(
            df[col1_name].dropna(), df[col2_name].dropna()
        )
        return jsonify({'test_name': 'Independent T-Test',
                        'columns': [col1_name, col2_name],
                        'statistic': float(stat), 'p_value': float(p_value),
                        'significant': bool(p_value < 0.05)})


HTML change — add column selectors to the hypothesis test form:

<!-- templates/review.html — hypothesis test form -->
<div class="form-group mt-2">
    <label class="form-label">Column 1</label>
    <select class="form-control" id="hypCol1"></select>
</div>
<div class="form-group mt-2">
    <label class="form-label">Column 2</label>
    <select class="form-control" id="hypCol2"></select>
</div> 
"""

# routes/review.py — add endpoint
@bp.route('/api/statistics/mutual_info', methods=['GET'])
def mutual_info():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400

    df, _ = current_app.dataset_store.load(dataset_id)
    from sklearn.feature_selection import mutual_info_regression
    from sklearn.preprocessing import LabelEncoder

    # Encode categoricals
    df_enc = df.copy()
    for col in df_enc.select_dtypes(include='object').columns:
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))

    df_enc = df_enc.select_dtypes(include=[np.number]).dropna()
    if df_enc.shape[1] < 2:
        return jsonify({'error': 'Need at least 2 columns'}), 400

    mi_matrix = {}
    cols = df_enc.columns.tolist()
    for target in cols:
        X = df_enc.drop(columns=[target])
        y = df_enc[target]
        mi = mutual_info_regression(X, y, random_state=42)
        mi_matrix[target] = dict(zip(X.columns, mi.tolist()))

    return jsonify({'mutual_info': mi_matrix, 'columns': cols})

@bp.route('/api/auto_insights', methods=['GET'])
def auto_insights():
    """Scan the dataset and surface automatically-discovered insights using statistical analysis."""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400

    df, name = current_app.dataset_store.load(dataset_id)
    insights = []

    # 1. High missingness columns
    missing_pct = (df.isnull().sum() / len(df) * 100)
    high_missing = missing_pct[missing_pct > 20].sort_values(ascending=False)
    if len(high_missing) > 0:
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': f'{len(high_missing)} column(s) with >20% missing data',
            'detail': f"Highest: '{high_missing.index[0]}' ({high_missing.iloc[0]:.1f}% missing)",
            'action': 'Go to Cleaning → Handle Missing Values'
        })

    # 2. Highly correlated features
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.shape[1] >= 2:
        corr = numeric_df.corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        high_corr = [(c, r, corr.loc[r, c]) for c in upper.columns
                      for r in upper.index if upper.loc[r, c] > 0.9]
        if high_corr:
            insights.append({
                'type': 'info',
                'icon': '🔗',
                'title': f'{len(high_corr)} highly correlated feature pair(s) (r > 0.9)',
                'detail': f"Strongest: '{high_corr[0][0]}' ↔ '{high_corr[0][1]}' (r={high_corr[0][2]:.3f})",
                'action': 'Consider dropping one of each pair before ML training'
            })

    # 3. Skewed distributions
    skewed = []
    for col in numeric_df.columns:
        sk = abs(float(stats.skew(df[col].dropna())))
        if sk > 1.5:
            skewed.append((col, sk))
    if skewed:
        skewed.sort(key=lambda x: x[1], reverse=True)
        insights.append({
            'type': 'info',
            'icon': '📐',
            'title': f'{len(skewed)} heavily skewed column(s)',
            'detail': f"Most skewed: '{skewed[0][0]}' (skewness={skewed[0][1]:.2f})",
            'action': 'Apply log transform in Cleaning → Bin/Transform'
        })

    # 4. Low-variance columns (near-constant)
    for col in numeric_df.columns:
        cv = df[col].std() / (abs(df[col].mean()) + 1e-10)
        if cv < 0.01:
            insights.append({
                'type': 'warning',
                'icon': '📉',
                'title': f"Near-constant column: '{col}'",
                'detail': f"Coefficient of variation = {cv:.4f}. This column provides little predictive value.",
                'action': 'Consider dropping in Cleaning → Column Operations'
            })

    # 5. Categorical columns with very high cardinality
    cat_cols = df.select_dtypes(include='object').columns
    for col in cat_cols:
        pct_unique = df[col].nunique() / len(df)
        if pct_unique > 0.9:
            insights.append({
                'type': 'warning',
                'icon': '🗝️',
                'title': f"High-cardinality column: '{col}' ({df[col].nunique()} unique values)",
                'detail': f"{pct_unique*100:.1f}% of rows are unique. May be an ID column.",
                'action': 'Drop or aggregate before ML training'
            })

    # 6. Duplicate rows
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        insights.append({
            'type': 'warning',
            'icon': '📋',
            'title': f'{dup_count:,} duplicate rows detected',
            'detail': f"{dup_count/len(df)*100:.1f}% of rows are exact duplicates.",
            'action': 'Remove duplicates in Cleaning → Auto Clean'
        })

    # 7. Imbalanced target candidates
    for col in cat_cols:
        if df[col].nunique() <= 10:
            vc = df[col].value_counts(normalize=True)
            if vc.iloc[0] > 0.80:
                insights.append({
                    'type': 'warning',
                    'icon': '⚖️',
                    'title': f"Potential class imbalance in '{col}'",
                    'detail': f"Dominant class: '{vc.index[0]}' ({vc.iloc[0]*100:.1f}% of rows)",
                    'action': 'Use SMOTE or class weighting in ML Studio'
                })

    return jsonify({'insights': insights[:10], 'total': len(insights)})

@bp.route('/api/ai_eda_report', methods=['POST'])
def ai_eda_report():
    """Generate AI-powered EDA report using Claude API."""
    dataset_id = session.get('dataset_id')
    api_key = session.get('api_key')
    
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    if not api_key:
        return jsonify({'error': 'API key required for AI features'}), 400

    df, name = current_app.dataset_store.load(dataset_id)
    numeric_summary = df.describe().to_dict()
    missing = df.isnull().sum().to_dict()
    dtypes = df.dtypes.astype(str).to_dict()

    dataset_context = f"""
Dataset: {name}
Shape: {df.shape[0]} rows × {df.shape[1]} columns
Column types: {dtypes}
Missing values per column: {missing}
Numeric summary: {numeric_summary}
Sample rows (first 3):
{df.head(3).to_dict(orient='records')}
"""

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=2000,
        system="You are an expert data analyst. Write a comprehensive EDA report in markdown. Be specific about the data.",
        messages=[{'role': 'user', 'content': f"Write a detailed EDA report for this dataset:\n{dataset_context}"}]
    )
    
    return jsonify({'report': response.content[0].text})
