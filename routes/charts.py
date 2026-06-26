from flask import Blueprint, render_template, session, jsonify, request, current_app
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import plotly.io as pio
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
    group_by = cfg.get('group_by', '')
    
    try:
        # Apply groupby aggregation if specified
        if group_by and x and y:
            agg_func_map = {
                'mean': 'mean',
                'sum': 'sum',
                'count': 'count',
                'median': 'median',
                'min': 'min',
                'max': 'max',
                'std': 'std'
            }
            if group_by in agg_func_map:
                df_grouped = df.groupby(x)[y].agg(agg_func_map[group_by]).reset_index()
                df = df_grouped
        
        # Apply aggregation if specified (legacy support)
        elif aggregation != 'none' and x and y:
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

        # --- New advanced chart types (lightweight implementations) ---
        elif chart_type == 'ecdf':
            # ECDF for a single numeric column (x)
            if x:
                s = df[x].dropna()
                if s.empty:
                    return jsonify({'error': 'No valid values for ECDF'}), 400
                xs = np.sort(s.values)
                ys = np.arange(1, len(xs) + 1) / len(xs)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', name=x, line=dict(color='rgb(99, 102, 241)')))
                fig.update_layout(template='plotly_white', title=f'ECDF: {x}', height=600)
            else:
                return jsonify({'error': 'X required for ecdf'}), 400

        elif chart_type == 'ridge':
            # Ridge-ish plot using multiple KDE curves stacked via y-offsets
            # x: numeric column; y: category column to facet by; color optional
            if x and y:
                cats = df[y].dropna().astype(str).value_counts().head(8).index.tolist()
                fig = go.Figure()
                for i, cat in enumerate(cats):
                    sub = df[df[y].astype(str) == cat]
                    vals = sub[x].dropna().values
                    if len(vals) < 10:
                        continue
                    # Use histogram as an approximation to density
                    hist = np.histogram(vals, bins=40, density=True)
                    bin_centers = 0.5 * (hist[1][:-1] + hist[1][1:])
                    dens = hist[0]
                    fig.add_trace(go.Scatter(x=bin_centers, y=dens + i, mode='lines', name=str(cat)))
                fig.update_layout(template='plotly_white', title=f'Ridge (approx KDE): {x} by {y}', height=600, showlegend=True)
            else:
                return jsonify({'error': 'X and Y required for ridge'}), 400

        elif chart_type == 'parallel_coords':
            # Parallel coordinates for multiple numeric columns. x should be list-like or first numeric column; use y as optional group.
            # Expect: x = comma-separated numeric columns; if not provided, take first 4 numeric.
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not num_cols:
                return jsonify({'error': 'No numeric columns available for parallel coords'}), 400
            use_cols = num_cols[:4]
            if x and isinstance(x, str) and ',' in x:
                use_cols = [c.strip() for c in x.split(',') if c.strip() in num_cols][:6] or use_cols
            fig = px.parallel_coordinates(df[use_cols + ([color] if color and color in df.columns else [])], dimensions=use_cols, color=color if color in df.columns else None, template='plotly_white')

        elif chart_type == 'correlation_network':
            # Correlation network graph among numeric columns with threshold.
            # x: correlation threshold (optional as string/float); y: optional comma list of columns
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(num_cols) < 2:
                return jsonify({'error': 'Need at least 2 numeric columns for correlation network'}), 400
            threshold = 0.7
            try:
                if x is not None:
                    threshold = float(x)
            except Exception:
                pass
            corr = df[num_cols].corr().abs()
            edges = []
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    if pd.notna(corr.iloc[i, j]) and corr.iloc[i, j] >= threshold:
                        edges.append((num_cols[i], num_cols[j], float(corr.iloc[i, j])))
            if not edges:
                fig = go.Figure()
                fig.update_layout(template='plotly_white', title='Correlation Network: no edges above threshold', height=600)
            else:
                # Circular layout (deterministic)
                nodes = sorted(list({a for a, b, w in edges} | {b for a, b, w in edges}))
                N = len(nodes)
                angle = np.linspace(0, 2 * np.pi, N, endpoint=False)
                pos = {nodes[i]: (float(np.cos(angle[i])), float(np.sin(angle[i]))) for i in range(N)}
                edge_traces = []
                for a, b, w in edges[:200]:
                    xa, ya = pos[a]
                    xb, yb = pos[b]
                    edge_traces.append(go.Scatter(x=[xa, xb], y=[ya, yb], mode='lines', line=dict(width=2 * w, color='rgba(99,102,241,0.6)'), hoverinfo='skip'))
                node_trace = go.Scatter(
                    x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes],
                    mode='markers+text',
                    text=nodes,
                    textposition='bottom center',
                    marker=dict(size=12, color='rgb(99, 102, 241)'),
                    hovertemplate='Node: %{text}<extra></extra>'
                )
                fig = go.Figure(data=edge_traces + [node_trace])
                fig.update_layout(template='plotly_white', title=f'Correlation Network (|r| >= {threshold})', height=600, xaxis_visible=False, yaxis_visible=False)

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

@bp.route('/api/build_multiple', methods=['POST'])
def build_multiple_charts():
    """Build multiple charts at once"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    configs = request.json.get('plots', [])
    
    results = []
    
    for idx, cfg in enumerate(configs):
        try:
            chart_type = cfg.get('chart_type', 'bar')
            x, y, color = cfg.get('x'), cfg.get('y'), cfg.get('color')
            size = cfg.get('size')
            group_by = cfg.get('group_by', '')
            
            # Apply groupby if specified
            plot_df = df.copy()
            if group_by and x and y:
                agg_func_map = {
                    'mean': 'mean',
                    'sum': 'sum',
                    'count': 'count',
                    'median': 'median'
                }
                if group_by in agg_func_map:
                    plot_df = plot_df.groupby(x)[y].agg(agg_func_map[group_by]).reset_index()
            
            # Build chart
            if chart_type == 'bar': 
                fig = px.bar(plot_df, x=x, y=y, color=color, template='plotly_white',
                           title=f'Bar Chart: {x} vs {y}')
            elif chart_type == 'line': 
                fig = px.line(plot_df, x=x, y=y, color=color, template='plotly_white',
                            title=f'Line Chart: {x} vs {y}')
            elif chart_type == 'scatter': 
                fig = px.scatter(plot_df, x=x, y=y, color=color, size=size, template='plotly_white',
                               title=f'Scatter Plot: {x} vs {y}')
            elif chart_type == 'histogram': 
                fig = px.histogram(plot_df, x=x, color=color, template='plotly_white',
                                 title=f'Histogram: {x}')
            elif chart_type == 'box': 
                fig = px.box(plot_df, x=x, y=y, color=color, template='plotly_white',
                           title=f'Box Plot: {x} vs {y}')
            elif chart_type == 'violin': 
                fig = px.violin(plot_df, x=x, y=y, color=color, template='plotly_white', box=True,
                              title=f'Violin Plot: {x} vs {y}')
            elif chart_type == 'pie':
                if x:
                    value_counts = plot_df[x].value_counts().head(10)
                    fig = px.pie(values=value_counts.values, names=value_counts.index,
                               template='plotly_white', title=f'Pie Chart: {x}')
                else:
                    continue
            elif chart_type == 'heatmap':
                numeric_df = plot_df.select_dtypes(include=[np.number])
                corr_matrix = numeric_df.corr()
                fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", template='plotly_white',
                              title='Correlation Heatmap')
            elif chart_type == 'area':
                fig = px.area(plot_df, x=x, y=y, color=color, template='plotly_white',
                            title=f'Area Chart: {x} vs {y}')
            elif chart_type == 'bubble':
                if size:
                    fig = px.scatter(plot_df, x=x, y=y, size=size, color=color,
                                   template='plotly_white', size_max=50,
                                   title=f'Bubble Chart: {x} vs {y}')
                else:
                    fig = px.scatter(plot_df, x=x, y=y, color=color, template='plotly_white',
                                   title=f'Bubble Chart: {x} vs {y}')
            else:
                continue
            
            fig.update_layout(margin=dict(l=50, r=50, t=60, b=50), height=500)
            
            results.append({
                'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
                'config': cfg
            })
        
        except Exception as e:
            print(f"Error generating plot {idx + 1}: {e}")
            continue
    
    return jsonify({'results': results, 'count': len(results)})

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

@bp.route('/api/quick/summary', methods=['POST'])
def quick_summary():
    """Generate comprehensive dashboard with exactly 20 diverse creative visualizations"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not numeric_cols and not categorical_cols:
        return jsonify({'error': 'No columns for summary'}), 400
    
    plots = []
    
    # Generate exactly 20 diverse and creative plot types
    plot_configs = []
    
    # 1-4. Histograms for first 4 numeric columns
    for col in numeric_cols[:4]:
        plot_configs.append(('histogram', col, None))
    
    # 5-7. Box plots for numeric columns
    for col in numeric_cols[:3]:
        plot_configs.append(('box', col, None))
    
    # 8-10. Bar charts for categorical columns
    for col in categorical_cols[:3]:
        plot_configs.append(('bar_categorical', col, None))
    
    # 11-13. Scatter plots (pairs of numeric columns)
    scatter_count = 0
    for i in range(min(3, len(numeric_cols))):
        for j in range(i+1, min(len(numeric_cols), i+2)):
            if scatter_count >= 3:
                break
            plot_configs.append(('scatter', numeric_cols[i], numeric_cols[j]))
            scatter_count += 1
    
    # 14. Violin plot
    if numeric_cols:
        plot_configs.append(('violin', numeric_cols[0], None))
    
    # 15. KDE density plot
    if numeric_cols:
        plot_configs.append(('kde', numeric_cols[0], None))
    
    # 16. Pie chart for first categorical
    if categorical_cols:
        plot_configs.append(('pie', categorical_cols[0], None))
    
    # 17. Line plot for trend
    if numeric_cols:
        plot_configs.append(('line', numeric_cols[0], None))
    
    # 18. Area plot
    if numeric_cols and len(numeric_cols) > 1:
        plot_configs.append(('area', numeric_cols[0], numeric_cols[1]))
    
    # 19. Heatmap (correlation matrix)
    if len(numeric_cols) >= 2:
        plot_configs.append(('heatmap', None, None))
    
    # 20. Missing values bar chart
    plot_configs.append(('missing_bar', None, None))
    
    # Ensure exactly 20 plots
    while len(plot_configs) < 20:
        # If we don't have enough plots, add a histogram of the first numeric column
        if numeric_cols:
            plot_configs.append(('histogram', numeric_cols[0], None))
        else:
            break
    
    # Limit to exactly 20 plots
    plot_configs = plot_configs[:20]
    
    # Generate each plot
    for plot_type, x_col, y_col in plot_configs:
        try:
            if plot_type == 'histogram':
                fig = px.histogram(df, x=x_col, template='plotly_white', 
                                  title=f'📊 Distribution: {x_col}',
                                  color_discrete_sequence=['#6366F1'],
                                  opacity=0.8)
                fig.update_traces(marker_line_color='white', marker_line_width=0.5)
            
            elif plot_type == 'box':
                fig = px.box(df, y=x_col, template='plotly_white',
                           title=f'📦 Box Plot: {x_col}',
                           color_discrete_sequence=['#10B981'],
                           points='outliers')
            
            elif plot_type == 'bar_categorical':
                value_counts = df[x_col].value_counts().head(10)
                fig = px.bar(x=value_counts.index, y=value_counts.values,
                           template='plotly_white', title=f'📊 Categories: {x_col}',
                           color_discrete_sequence=['#F59E0B'])
                fig.update_traces(marker_line_color='white', marker_line_width=0.5)
            
            elif plot_type == 'scatter':
                fig = px.scatter(df, x=x_col, y=y_col, template='plotly_white',
                               title=f'🔍 Relationship: {x_col} vs {y_col}',
                               color_discrete_sequence=['#EC4899'],
                               opacity=0.6)
                fig.update_traces(marker_size=6)
            
            elif plot_type == 'violin':
                fig = px.violin(df, y=x_col, template='plotly_white',
                              title=f'🎻 Violin Plot: {x_col}',
                              color_discrete_sequence=['#A855F7'],
                              box=True, points='all')
            
            elif plot_type == 'kde':
                fig = px.density_contour(df, x=x_col, y=x_col, template='plotly_white',
                                       title=f'🌊 Density Contour: {x_col}',
                                       color_continuous_scale='Viridis')
            
            elif plot_type == 'pie':
                value_counts = df[x_col].value_counts().head(8)
                fig = px.pie(values=value_counts.values, names=value_counts.index,
                           template='plotly_white', title=f'🥧 Proportions: {x_col}',
                           color_discrete_sequence=px.colors.qualitative.Set2)
            
            elif plot_type == 'line':
                df_reset = df.reset_index()
                fig = px.line(df_reset, x='index', y=x_col, template='plotly_white',
                            title=f'📈 Trend: {x_col}',
                            color_discrete_sequence=['#22C55E'])
                fig.update_traces(line_width=2)
            
            elif plot_type == 'area':
                df_reset = df.reset_index()
                fig = px.area(df_reset, x='index', y=[x_col, y_col], template='plotly_white',
                            title=f'📉 Area Chart: {x_col} & {y_col}',
                            color_discrete_sequence=['#3B82F6', '#EF4444'])
                fig.update_traces(opacity=0.6)
            
            elif plot_type == 'heatmap':
                numeric_df = df[numeric_cols[:8]].corr()
                fig = px.imshow(numeric_df, text_auto='.2f', aspect="auto",
                              template='plotly_white', title='🔥 Correlation Heatmap',
                              color_continuous_scale='RdBu_r')
            
            elif plot_type == 'missing_bar':
                missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
                missing_df = missing_pct[missing_pct > 0].head(10).reset_index()
                missing_df.columns = ['Column', 'Missing %']
                
                if not missing_df.empty:
                    fig = px.bar(missing_df, x='Missing %', y='Column', orientation='h',
                               template='plotly_white', title='⚠️ Missing Values',
                               color='Missing %', color_continuous_scale='Reds')
                else:
                    # If no missing values, show a success message plot
                    fig = go.Figure()
                    fig.add_annotation(text="✅ No Missing Values!", 
                                     xref="paper", yref="paper",
                                     x=0.5, y=0.5, showarrow=False,
                                     font=dict(size=24, color="#10B981"))
                    fig.update_layout(title='Data Quality Check', height=400)
            
            fig.update_layout(margin=dict(l=50, r=50, t=60, b=50), height=400)
            plots.append(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
        
        except Exception as e:
            print(f"Error generating {plot_type}: {e}")
            continue
    
    return jsonify({'plots': plots, 'count': len(plots)})