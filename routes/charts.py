from flask import Blueprint, render_template, session, jsonify, request, current_app
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import json
import numpy as np

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
    chart_type = cfg.get('chart_type', 'bar')
    x, y, color = cfg.get('x'), cfg.get('y'), cfg.get('color')
    size = cfg.get('size')
    facet = cfg.get('facet')
    aggregation = cfg.get('aggregation', 'none')
    sort_by = cfg.get('sort', 'none')
    
    try:
        # Apply aggregation if specified
        if aggregation != 'none' and x and y:
            agg_func = getattr(df.groupby(x)[y], aggregation)
            df = agg_func().reset_index()
        
        # Apply sorting if specified
        if sort_by != 'none' and y:
            ascending = sort_by == 'asc'
            df = df.sort_values(by=y, ascending=ascending)
        
        # Build chart based on type
        if chart_type == 'bar': 
            fig = px.bar(df, x=x, y=y, color=color, template='plotly_white')
        elif chart_type == 'line': 
            fig = px.line(df, x=x, y=y, color=color, template='plotly_white')
        elif chart_type == 'scatter': 
            fig = px.scatter(df, x=x, y=y, color=color, size=size, template='plotly_white')
        elif chart_type == 'histogram': 
            fig = px.histogram(df, x=x, color=color, template='plotly_white')
        elif chart_type == 'box': 
            fig = px.box(df, x=x, y=y, color=color, template='plotly_white')
        elif chart_type == 'violin': 
            fig = px.violin(df, x=x, y=y, color=color, template='plotly_white', box=True)
        elif chart_type == 'heatmap':
            numeric_df = df.select_dtypes(include=[np.number])
            corr_matrix = numeric_df.corr()
            fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", template='plotly_white')
        elif chart_type == 'pie':
            if x:
                value_counts = df[x].value_counts().head(10)
                fig = px.pie(values=value_counts.values, names=value_counts.index, template='plotly_white')
            else:
                return jsonify({'error': 'Please select a column for pie chart'}), 400
        elif chart_type == 'area':
            fig = px.area(df, x=x, y=y, color=color, template='plotly_white')
        elif chart_type == 'bubble':
            if size:
                fig = px.scatter(df, x=x, y=y, size=size, color=color, template='plotly_white', size_max=50)
            else:
                fig = px.scatter(df, x=x, y=y, color=color, template='plotly_white')
        elif chart_type == 'density':
            if x:
                fig = px.density_contour(df, x=x, y=y, color=color, template='plotly_white')
            else:
                return jsonify({'error': 'X axis required for density plot'}), 400
        elif chart_type == 'treemap':
            if x and y:
                fig = px.treemap(df, path=[x], values=y, color=y, template='plotly_white')
            else:
                return jsonify({'error': 'X and Y required for treemap'}), 400
        elif chart_type == 'sunburst':
            if x and y:
                cols = [x] + ([color] if color else [])
                fig = px.sunburst(df, path=cols, values=y, template='plotly_white')
            else:
                return jsonify({'error': 'X and Y required for sunburst'}), 400
        elif chart_type == 'funnel':
            if x and y:
                fig = px.funnel(df, x=y, y=x, template='plotly_white')
            else:
                return jsonify({'error': 'X and Y required for funnel chart'}), 400
        elif chart_type == 'radar':
            # Radar chart requires specific data structure
            if x and y:
                fig = px.line_polar(df, r=y, theta=x, color=color, template='plotly_white', line_close=True)
            else:
                return jsonify({'error': 'X and Y required for radar chart'}), 400
        else: 
            fig = px.bar(df, x=x, y=y, template='plotly_white')
        
        # Apply faceting if specified
        if facet and facet in df.columns:
            fig.facet_wrap(facet)
        
        fig.update_layout(
            margin=dict(l=40, r=40, t=60, b=40),
            font=dict(family='Inter, sans-serif'),
            hovermode='closest',
            height=600
        )
        
        return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/api/auto_viz', methods=['GET'])
def auto_viz():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Smart recommendation logic
    if len(numeric_cols) >= 2:
        # Suggest correlation heatmap or scatter
        fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], 
                        template='plotly_white', title=f'{numeric_cols[0]} vs {numeric_cols[1]}')
        recommendation = f"Scatter plot showing relationship between {numeric_cols[0]} and {numeric_cols[1]}"
    elif len(numeric_cols) == 1:
        # Single numeric - histogram
        fig = px.histogram(df, x=numeric_cols[0], template='plotly_white', 
                          title=f'Distribution of {numeric_cols[0]}')
        recommendation = f"Histogram showing distribution of {numeric_cols[0]}"
    elif len(categorical_cols) >= 1:
        # Categorical - bar chart of value counts
        col = categorical_cols[0]
        value_counts = df[col].value_counts().head(10)
        fig = px.bar(x=value_counts.index, y=value_counts.values, template='plotly_white',
                    title=f'Top 10 {col} values')
        recommendation = f"Bar chart of top 10 {col} categories"
    else:
        return jsonify({'error': 'No suitable columns found for visualization'}), 400
    
    fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
    
    return jsonify({
        'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        'recommendation': recommendation
    })

@bp.route('/api/quick/correlation', methods=['GET'])
def quick_correlation():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.shape[1] < 2:
        return jsonify({'error': 'Need at least 2 numeric columns'}), 400
    
    corr_matrix = numeric_df.corr()
    fig = px.imshow(corr_matrix, text_auto='.2f', aspect="auto", 
                   template='plotly_white', title='Correlation Matrix',
                   color_continuous_midpoint=0)
    fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
    
    return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})

@bp.route('/api/quick/distribution', methods=['GET'])
def quick_distribution():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        return jsonify({'error': 'No numeric columns found'}), 400
    
    # Create subplots for each numeric column
    from plotly.subplots import make_subplots
    n_cols = min(len(numeric_cols), 4)  # Max 4 columns
    fig = make_subplots(rows=1, cols=n_cols, subplot_titles=numeric_cols[:n_cols])
    
    for i, col in enumerate(numeric_cols[:n_cols]):
        fig.add_trace(go.Histogram(x=df[col], name=col, showlegend=False), row=1, col=i+1)
    
    fig.update_layout(height=400, template='plotly_white', title_text='Distribution Overview')
    fig.update_xaxes(title_text='Value')
    fig.update_yaxes(title_text='Count')
    
    return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})

@bp.route('/api/quick/missing', methods=['GET'])
def quick_missing():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    
    # Calculate missing percentage per column
    missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
    missing_df = missing_pct[missing_pct > 0].reset_index()
    missing_df.columns = ['Column', 'Missing %']
    
    if missing_df.empty:
        return jsonify({'error': 'No missing values found! Data is clean.'}), 400
    
    fig = px.bar(missing_df.head(20), x='Missing %', y='Column', orientation='h',
                template='plotly_white', title='Missing Values by Column (Top 20)',
                color='Missing %', color_continuous_scale='Reds')
    fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
    
    return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})

@bp.route('/api/quick/summary', methods=['GET'])
def quick_summary():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not numeric_cols and not categorical_cols:
        return jsonify({'error': 'No columns for summary'}), 400
    
    from plotly.subplots import make_subplots
    import math
    
    # Create comprehensive dashboard with multiple subplots
    n_plots = min(len(numeric_cols) + len(categorical_cols), 16)  # Max 16 plots
    n_cols = 4
    n_rows = math.ceil(n_plots / n_cols)
    
    fig = make_subplots(
        rows=n_rows, 
        cols=n_cols,
        subplot_titles=[],
        vertical_spacing=0.08,
        horizontal_spacing=0.08
    )
    
    plot_idx = 1
    
    # Add histograms for numeric columns
    for i, col in enumerate(numeric_cols[:8]):  # Max 8 numeric
        row = (plot_idx - 1) // n_cols + 1
        col_pos = (plot_idx - 1) % n_cols + 1
        
        fig.add_trace(
            go.Histogram(x=df[col], name=col, showlegend=False, marker_color='rgb(99, 102, 241)'),
            row=row, col=col_pos
        )
        fig.update_xaxes(title_text=col, row=row, col=col_pos)
        plot_idx += 1
    
    # Add bar charts for categorical columns
    for i, col in enumerate(categorical_cols[:8]):  # Max 8 categorical
        if plot_idx > 16:
            break
            
        row = (plot_idx - 1) // n_cols + 1
        col_pos = (plot_idx - 1) % n_cols + 1
        
        value_counts = df[col].value_counts().head(10)
        
        fig.add_trace(
            go.Bar(x=value_counts.index, y=value_counts.values, name=col, showlegend=False, 
                  marker_color='rgb(16, 185, 129)'),
            row=row, col=col_pos
        )
        fig.update_xaxes(title_text=col, tickangle=45, row=row, col=col_pos)
        plot_idx += 1
    
    fig.update_layout(
        height=400 * n_rows,
        width=1600,
        template='plotly_white',
        title_text='Comprehensive Data Summary Dashboard',
        showlegend=False
    )
    
    return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
