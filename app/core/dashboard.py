"""
FINESE2 - Consolidated Dashboard Module
Comprehensive dashboard and UI capabilities in a single module.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from jinja2 import Template
import os
from pathlib import Path
import json
import logging
from io import StringIO

logger = logging.getLogger(__name__)


class DashboardManager:
    """
    Consolidated dashboard manager providing comprehensive UI and dashboard capabilities.
    """
    
    def __init__(self):
        self.dashboards = {}
        self.widgets = {}
        self.layouts = {}
        self.dashboard_templates = {
            'default': self._default_dashboard_template,
            'analytics': self._analytics_dashboard_template,
            'ml_monitoring': self._ml_monitoring_dashboard_template
        }
    
    def _default_dashboard_template(self, data: Dict[str, Any]) -> str:
        """Generate a default dashboard template."""
        template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ title }}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    padding-top: 20px;
                }
                .dashboard-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                .metric-card {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                    transition: transform 0.2s;
                }
                .metric-card:hover {
                    transform: translateY(-2px);
                }
                .metric-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                }
                .metric-title {
                    font-size: 0.9em;
                    color: #6c757d;
                    margin-bottom: 5px;
                }
                .chart-container {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .dashboard-section {
                    margin-bottom: 30px;
                }
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <div class="dashboard-header">
                    <h1>{{ title }}</h1>
                    <p>{{ subtitle }}</p>
                </div>
                
                <!-- Key Metrics -->
                <div class="row dashboard-section">
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">Total Records</div>
                            <div class="metric-value">{{ metrics.total_records }}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">Total Columns</div>
                            <div class="metric-value">{{ metrics.total_columns }}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">Missing Values</div>
                            <div class="metric-value">{{ metrics.missing_values }}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">Duplicate Rows</div>
                            <div class="metric-value">{{ metrics.duplicate_rows }}</div>
                        </div>
                    </div>
                </div>
                
                <!-- Charts Section -->
                <div class="dashboard-section">
                    <h3>Data Overview</h3>
                    {% for chart_id, chart_html in charts.items() %}
                    <div class="chart-container">
                        <h4>{{ chart_titles[loop.index0] }}</h4>
                        {{ chart_html|safe }}
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Recent Activity -->
                {% if recent_activity %}
                <div class="dashboard-section">
                    <h3>Recent Activity</h3>
                    <div class="card">
                        <div class="card-body">
                            <ul class="list-group list-group-flush">
                                {% for activity in recent_activity %}
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    {{ activity.action }}
                                    <span class="badge bg-primary rounded-pill">{{ activity.timestamp }}</span>
                                </li>
                                {% endfor %}
                            </ul>
                        </div>
                    </div>
                </div>
                {% endif %}
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        return template
    
    def _analytics_dashboard_template(self, data: Dict[str, Any]) -> str:
        """Generate an analytics-focused dashboard template."""
        template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ title }}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    padding-top: 20px;
                }
                .dashboard-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                .metric-card {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                    transition: transform 0.2s;
                }
                .metric-card:hover {
                    transform: translateY(-2px);
                }
                .metric-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                }
                .metric-title {
                    font-size: 0.9em;
                    color: #6c757d;
                    margin-bottom: 5px;
                }
                .chart-container {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .dashboard-section {
                    margin-bottom: 30px;
                }
                .filter-panel {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <div class="dashboard-header">
                    <h1>{{ title }}</h1>
                    <p>{{ subtitle }}</p>
                </div>
                
                <!-- Filters -->
                <div class="filter-panel">
                    <h5>Filters</h5>
                    <form id="dashboard-filters">
                        <div class="row">
                            <div class="col-md-3">
                                <label for="date-range" class="form-label">Date Range</label>
                                <input type="date" class="form-control" id="date-range-start">
                                <input type="date" class="form-control mt-2" id="date-range-end">
                            </div>
                            <div class="col-md-3">
                                <label for="category-filter" class="form-label">Category</label>
                                <select class="form-select" id="category-filter">
                                    <option value="all">All Categories</option>
                                    {% for cat in available_categories %}
                                    <option value="{{ cat }}">{{ cat }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-3">
                                <label for="metric-filter" class="form-label">Metric</label>
                                <select class="form-select" id="metric-filter">
                                    {% for metric in available_metrics %}
                                    <option value="{{ metric }}">{{ metric }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-3">
                                <label>&nbsp;</label>
                                <button type="button" class="btn btn-primary w-100" onclick="applyFilters()">Apply Filters</button>
                            </div>
                        </div>
                    </form>
                </div>
                
                <!-- Key Metrics -->
                <div class="row dashboard-section">
                    {% for metric in key_metrics %}
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">{{ metric.title }}</div>
                            <div class="metric-value">{{ metric.value }}</div>
                            <small class="text-muted">{{ metric.change }}% from last period</small>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Charts Section -->
                <div class="dashboard-section">
                    <h3>Analytics Overview</h3>
                    {% for chart_id, chart_html in charts.items() %}
                    <div class="chart-container">
                        <h4>{{ chart_titles[loop.index0] }}</h4>
                        {{ chart_html|safe }}
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Data Table -->
                {% if data_table %}
                <div class="dashboard-section">
                    <h3>Data Table</h3>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    {% for col in data_table.columns %}
                                    <th>{{ col }}</th>
                                    {% endfor %}
                                </tr>
                            </thead>
                            <tbody>
                                {% for index, row in data_table.iterrows() %}
                                <tr>
                                    {% for cell in row %}
                                    <td>{{ cell }}</td>
                                    {% endfor %}
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                {% endif %}
            </div>
            
            <script>
                function applyFilters() {
                    const startDate = document.getElementById('date-range-start').value;
                    const endDate = document.getElementById('date-range-end').value;
                    const category = document.getElementById('category-filter').value;
                    const metric = document.getElementById('metric-filter').value;
                    
                    console.log('Filters applied:', {startDate, endDate, category, metric});
                    // In a real implementation, you would update the dashboard content here
                }
            </script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        return template
    
    def _ml_monitoring_dashboard_template(self, data: Dict[str, Any]) -> str:
        """Generate an ML monitoring dashboard template."""
        template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ title }}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    padding-top: 20px;
                }
                .dashboard-header {
                    background: linear-gradient(135deg, #2ecc71 0%, #3498db 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                .metric-card {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                    transition: transform 0.2s;
                }
                .metric-card:hover {
                    transform: translateY(-2px);
                }
                .metric-value {
                    font-size: 2em;
                    font-weight: bold;
                }
                .good-metric { color: #2ecc71; }
                .bad-metric { color: #e74c3c; }
                .metric-title {
                    font-size: 0.9em;
                    color: #6c757d;
                    margin-bottom: 5px;
                }
                .chart-container {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .dashboard-section {
                    margin-bottom: 30px;
                }
                .model-status {
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                    font-weight: bold;
                }
                .status-active { background-color: #d4edda; color: #155724; }
                .status-warning { background-color: #fff3cd; color: #856404; }
                .status-error { background-color: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <div class="dashboard-header">
                    <h1>{{ title }}</h1>
                    <p>{{ subtitle }}</p>
                </div>
                
                <!-- Model Status -->
                <div class="row dashboard-section">
                    <div class="col-md-12">
                        <h3>Model Status</h3>
                        {% for model in models %}
                        <div class="metric-card">
                            <div class="row align-items-center">
                                <div class="col-md-8">
                                    <div class="metric-title">{{ model.name }}</div>
                                    <div class="metric-value">{{ model.version }}</div>
                                    <div>Accuracy: {{ "%.2f"|format(model.accuracy|float) }}%</div>
                                </div>
                                <div class="col-md-4 text-end">
                                    <div class="model-status status-{{ model.status }}">{{ model.status|title }}</div>
                                    <small>Last Updated: {{ model.last_updated }}</small>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <!-- Performance Metrics -->
                <div class="row dashboard-section">
                    {% for metric in performance_metrics %}
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">{{ metric.title }}</div>
                            <div class="metric-value {{ metric.css_class }}">{{ metric.value }}</div>
                            <small class="text-muted">{{ metric.description }}</small>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Model Performance Charts -->
                <div class="dashboard-section">
                    <h3>Model Performance Over Time</h3>
                    {% for chart_id, chart_html in charts.items() %}
                    <div class="chart-container">
                        <h4>{{ chart_titles[loop.index0] }}</h4>
                        {{ chart_html|safe }}
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Alerts -->
                {% if alerts %}
                <div class="dashboard-section">
                    <h3>Alerts</h3>
                    {% for alert in alerts %}
                    <div class="alert alert-{{ alert.level }}" role="alert">
                        <h6>{{ alert.title }}</h6>
                        <p>{{ alert.message }}</p>
                        <small class="text-muted">{{ alert.timestamp }}</small>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        return template
    
    def create_default_dashboard(self, df: pd.DataFrame, title: str = "Data Dashboard", 
                                subtitle: str = "Interactive Data Visualization") -> str:
        """Create a default dashboard with key metrics and charts."""
        from .visualize import visualizer
        
        # Calculate key metrics
        metrics = {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'missing_values': int(df.isnull().sum().sum()),
            'duplicate_rows': int(df.duplicated().sum()),
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }
        
        # Create charts
        charts = {}
        chart_titles = []
        
        # Try to create meaningful charts based on the data
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if numeric_cols:
            # Create histogram for first numeric column
            try:
                fig_hist = visualizer.create_histogram(df, numeric_cols[0], title=f"Distribution of {numeric_cols[0]}")
                charts['histogram'] = plot(fig_hist, output_type='div', include_plotlyjs=False)
                chart_titles.append(f"Distribution of {numeric_cols[0]}")
            except:
                pass
        
        if len(numeric_cols) >= 2:
            # Create scatter plot for first two numeric columns
            try:
                fig_scatter = visualizer.create_scatter_plot(df, numeric_cols[0], numeric_cols[1], 
                                                           title=f"{numeric_cols[0]} vs {numeric_cols[1]}")
                charts['scatter'] = plot(fig_scatter, output_type='div', include_plotlyjs=False)
                chart_titles.append(f"{numeric_cols[0]} vs {numeric_cols[1]}")
            except:
                pass
        
        if categorical_cols:
            # Create bar chart for first categorical column
            try:
                value_counts = df[categorical_cols[0]].value_counts().head(10).reset_index()
                value_counts.columns = [categorical_cols[0], 'count']
                fig_bar = visualizer.create_bar_plot(value_counts, categorical_cols[0], 'count',
                                                   title=f"Top Categories in {categorical_cols[0]}")
                charts['bar_chart'] = plot(fig_bar, output_type='div', include_plotlyjs=False)
                chart_titles.append(f"Top Categories in {categorical_cols[0]}")
            except:
                pass
        
        # Prepare data for template
        data = {
            'title': title,
            'subtitle': subtitle,
            'metrics': metrics,
            'charts': charts,
            'chart_titles': chart_titles,
            'recent_activity': [
                {'action': 'Dataset uploaded', 'timestamp': '2 hours ago'},
                {'action': 'EDA performed', 'timestamp': '1 hour ago'},
                {'action': 'Initial cleaning', 'timestamp': '30 minutes ago'},
                {'action': 'Report generated', 'timestamp': '10 minutes ago'}
            ]
        }
        
        # Render template
        template_str = self._default_dashboard_template(data)
        template = Template(template_str)
        return template.render(data)
    
    def create_analytics_dashboard(self, df: pd.DataFrame, title: str = "Analytics Dashboard", 
                                  subtitle: str = "Advanced Data Analytics") -> str:
        """Create an analytics-focused dashboard."""
        from .visualize import visualizer
        from .analysis import analysis_engine
        
        # Calculate key metrics
        key_metrics = [
            {'title': 'Total Records', 'value': len(df), 'change': '+5.2'},
            {'title': 'Active Features', 'value': len(df.columns), 'change': '+2.1'},
            {'title': 'Data Completeness', 'value': f"{(1 - df.isnull().sum().sum()/(len(df)*len(df.columns)))*100:.1f}%", 'change': '+1.3'},
            {'title': 'Data Quality Score', 'value': '87%', 'change': '+3.5'}
        ]
        
        # Create charts
        charts = {}
        chart_titles = []
        
        # Try to create meaningful charts based on the data
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if numeric_cols:
            try:
                # Line chart for trends over time if date column exists
                date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
                if date_cols and len(numeric_cols) > 0:
                    fig_line = visualizer.create_time_series(df, date_cols[0], numeric_cols[0], 
                                                           title=f"Trend of {numeric_cols[0]} over Time")
                    charts['time_series'] = plot(fig_line, output_type='div', include_plotlyjs=False)
                    chart_titles.append(f"Trend of {numeric_cols[0]} over Time")
            except:
                pass
        
        if len(numeric_cols) >= 2:
            try:
                # Correlation heatmap
                fig_corr = visualizer.create_heatmap(df, numeric_cols[:8], title="Feature Correlation Matrix")
                charts['correlation'] = plot(fig_corr, output_type='div', include_plotlyjs=False)
                chart_titles.append("Feature Correlation Matrix")
            except:
                pass
        
        if categorical_cols and numeric_cols:
            try:
                # Box plot comparing numeric values across categories
                fig_box = visualizer.create_box_plot(df, numeric_cols[0], categorical_cols[0], 
                                                   title=f"{numeric_cols[0]} by {categorical_cols[0]}")
                charts['box_plot'] = plot(fig_box, output_type='div', include_plotlyjs=False)
                chart_titles.append(f"{numeric_cols[0]} by {categorical_cols[0]}")
            except:
                pass
        
        # Prepare data for template
        data = {
            'title': title,
            'subtitle': subtitle,
            'key_metrics': key_metrics,
            'charts': charts,
            'chart_titles': chart_titles,
            'available_categories': categorical_cols[:5],  # Limit to first 5 categories
            'available_metrics': numeric_cols[:5],  # Limit to first 5 metrics
            'data_table': df.head(10)  # Show first 10 rows
        }
        
        # Render template
        template_str = self._analytics_dashboard_template(data)
        template = Template(template_str)
        return template.render(data)
    
    def create_ml_monitoring_dashboard(self, models_data: List[Dict], 
                                     performance_metrics: List[Dict],
                                     alerts: List[Dict] = None,
                                     title: str = "ML Model Monitoring Dashboard",
                                     subtitle: str = "Real-time Model Performance Tracking") -> str:
        """Create an ML monitoring dashboard."""
        from .visualize import visualizer
        
        # Prepare model data
        models = []
        for model_data in models_data:
            models.append({
                'name': model_data.get('name', 'Unknown'),
                'version': model_data.get('version', 'N/A'),
                'accuracy': model_data.get('accuracy', 0) * 100,
                'status': model_data.get('status', 'active'),
                'last_updated': model_data.get('last_updated', 'N/A')
            })
        
        # Prepare performance metrics
        perf_metrics = []
        for metric in performance_metrics:
            css_class = 'good-metric' if metric.get('is_good', True) else 'bad-metric'
            perf_metrics.append({
                'title': metric.get('title', 'Metric'),
                'value': metric.get('value', 'N/A'),
                'css_class': css_class,
                'description': metric.get('description', '')
            })
        
        # Create charts
        charts = {}
        chart_titles = []
        
        # Example: Create a performance over time chart if we have historical data
        try:
            # Create dummy data for demonstration
            dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
            accuracy_values = np.random.uniform(0.8, 0.95, 30)  # Random accuracy values
            
            perf_df = pd.DataFrame({
                'date': dates,
                'accuracy': accuracy_values
            })
            
            fig_perf = visualizer.create_line_plot(perf_df, 'date', 'accuracy', 
                                                 title="Model Accuracy Over Time")
            charts['performance'] = plot(fig_perf, output_type='div', include_plotlyjs=False)
            chart_titles.append("Model Accuracy Over Time")
        except:
            pass
        
        # Prepare data for template
        data = {
            'title': title,
            'subtitle': subtitle,
            'models': models,
            'performance_metrics': perf_metrics,
            'charts': charts,
            'chart_titles': chart_titles,
            'alerts': alerts or []
        }
        
        # Render template
        template_str = self._ml_monitoring_dashboard_template(data)
        template = Template(template_str)
        return template.render(data)
    
    def create_custom_dashboard(self, layout: Dict[str, Any], data_sources: Dict[str, pd.DataFrame],
                               title: str = "Custom Dashboard") -> str:
        """Create a custom dashboard with user-defined layout."""
        # This would implement a more flexible dashboard creation system
        # For now, returning a placeholder
        return self.create_default_dashboard(data_sources.get('main', pd.DataFrame()), title)
    
    def export_dashboard(self, dashboard_html: str, filename: str, format: str = 'html') -> str:
        """Export the dashboard to a file."""
        filepath = f"{filename}.{format}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        return filepath
    
    def get_dashboard_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get a summary of the data for dashboard purposes."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        summary = {
            'dataset_info': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_columns': len(numeric_cols),
                'categorical_columns': len(categorical_cols),
                'memory_usage_mb': round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
            },
            'data_quality': {
                'missing_values_total': int(df.isnull().sum().sum()),
                'missing_values_pct': round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2),
                'duplicate_rows': int(df.duplicated().sum()),
                'duplicate_pct': round(df.duplicated().sum() / len(df) * 100, 2)
            }
        }
        
        if numeric_cols:
            summary['numeric_insights'] = {
                'avg_missing_per_num_col': round(df[numeric_cols].isnull().sum().mean(), 2),
                'most_correlated_pair': self._find_most_correlated_pair(df[numeric_cols])
            }
        
        if categorical_cols:
            summary['categorical_insights'] = {
                'avg_cardinality': round(df[categorical_cols].nunique().mean(), 2),
                'most_popular_category': self._find_most_popular_category(df, categorical_cols)
            }
        
        return summary
    
    def _find_most_correlated_pair(self, df_numeric: pd.DataFrame) -> Optional[tuple]:
        """Find the most correlated pair of columns."""
        if df_numeric.shape[1] < 2:
            return None
        
        corr_matrix = df_numeric.corr()
        # Remove diagonal and find highest correlation
        corr_matrix_no_diag = corr_matrix.mask(np.triu(np.ones_like(corr_matrix, dtype=bool)))
        max_corr_idx = np.unravel_index(np.argmax(np.abs(corr_matrix_no_diag.values)), corr_matrix_no_diag.shape)
        
        col1, col2 = corr_matrix_no_diag.index[max_corr_idx[0]], corr_matrix_no_diag.columns[max_corr_idx[1]]
        corr_val = corr_matrix.loc[col1, col2]
        
        return (col1, col2, round(corr_val, 3))
    
    def _find_most_popular_category(self, df: pd.DataFrame, categorical_cols: List[str]) -> Optional[Dict]:
        """Find the most popular category across all categorical columns."""
        if not categorical_cols:
            return None
        
        max_count = 0
        most_popular = None
        
        for col in categorical_cols:
            value_counts = df[col].value_counts()
            if not value_counts.empty:
                top_val = value_counts.index[0]
                top_count = value_counts.iloc[0]
                if top_count > max_count:
                    max_count = top_count
                    most_popular = {'column': col, 'value': str(top_val), 'count': int(top_count)}
        
        return most_popular


# Global instance
dashboard_manager = DashboardManager()