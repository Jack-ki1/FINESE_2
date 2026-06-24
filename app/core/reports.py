"""
FINESE2 - Consolidated Reports Module
Comprehensive reporting capabilities in a single module.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json
import csv
from datetime import datetime
import os
from io import StringIO
import base64
from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot
import warnings
warnings.filterwarnings('ignore')

class ReportGenerator:
    """
    Consolidated report generator providing comprehensive reporting capabilities.
    """
    
    def __init__(self):
        self.reports = {}
        self.report_templates = {
            'basic': self._basic_report_template,
            'eda': self._eda_report_template,
            'ml': self._ml_report_template,
            'comparison': self._comparison_report_template
        }
    
    def generate_report(self, df: pd.DataFrame, report_type: str = 'basic', title: str = "Report") -> Dict[str, Any]:
        """Generate a report based on the specified type."""
        report_methods = {
            'basic': self.generate_basic_report,
            'eda': self.generate_eda_report,
            'ml': lambda df, t: self.generate_ml_report({'name': 'N/A'}, {}, df),
            'comparison': lambda df, t: {'error': 'Comparison requires multiple models'}
        }
        
        if report_type not in report_methods:
            raise ValueError(f"Unsupported report type: {report_type}. Supported types: {list(report_methods.keys())}")
        
        # Call the appropriate report method
        method = report_methods[report_type]
        report_content = method(df, title)
        
        return {
            'title': title,
            'type': report_type,
            'content': report_content,
            'generated_at': pd.Timestamp.now().isoformat()
        }
    
    def _basic_report_template(self, data: Dict[str, Any]) -> str:
        """Generate a basic report template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #2E86AB; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; }
                .section { margin: 20px 0; }
                .metric { display: inline-block; margin: 10px; padding: 15px; 
                         background-color: #f9f9f9; border-radius: 5px; min-width: 200px; }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>
            <p>Generated on: {{ timestamp }}</p>
            
            <div class="section">
                <h2>Dataset Overview</h2>
                <div class="metric">Rows: {{ overview.rows }}</div>
                <div class="metric">Columns: {{ overview.columns }}</div>
                <div class="metric">Memory Usage: {{ overview.memory_usage }} MB</div>
            </div>
            
            {% if overview.numeric_summary %}
            <div class="section">
                <h2>Numeric Columns Summary</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            {% for col in overview.numeric_summary.keys() %}
                            <th>{{ col }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for metric in overview.numeric_summary[list(overview.numeric_summary.keys())[0]].keys() %}
                        <tr>
                            <td>{{ metric }}</td>
                            {% for col in overview.numeric_summary.keys() %}
                            <td>{{ "%.2f"|format(overview.numeric_summary[col][metric]|float) }}</td>
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
            
            {% if overview.missing_values %}
            <div class="section">
                <h2>Missing Values</h2>
                <table>
                    <thead>
                        <tr><th>Column</th><th>Count</th><th>Percentage</th></tr>
                    </thead>
                    <tbody>
                        {% for col, count in overview.missing_values.items() %}
                        <tr>
                            <td>{{ col }}</td>
                            <td>{{ count }}</td>
                            <td>{{ "%.2f"|format((count / overview.rows * 100)|float) }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </body>
        </html>
        """
        return template
    
    def _eda_report_template(self, data: Dict[str, Any]) -> str:
        """Generate an EDA-focused report template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #2E86AB; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; }
                .section { margin: 20px 0; }
                .metric { display: inline-block; margin: 10px; padding: 15px; 
                         background-color: #f9f9f9; border-radius: 5px; min-width: 200px; }
                .chart-container { margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>
            <p>Generated on: {{ timestamp }}</p>
            
            <div class="section">
                <h2>Dataset Overview</h2>
                <div class="metric">Rows: {{ overview.rows }}</div>
                <div class="metric">Columns: {{ overview.columns }}</div>
                <div class="metric">Numeric Columns: {{ overview.numeric_columns }}</div>
                <div class="metric">Categorical Columns: {{ overview.categorical_columns }}</div>
            </div>
            
            {% if distributions %}
            <div class="section">
                <h2>Distribution Analysis</h2>
                {% for col, dist_info in distributions.items() %}
                <h3>{{ col }}</h3>
                <ul>
                    {% for key, value in dist_info.items() %}
                    <li>{{ key }}: {{ value }}</li>
                    {% endfor %}
                </ul>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if correlation %}
            <div class="section">
                <h2>Correlation Analysis</h2>
                {% if correlation.high_correlation_pairs %}
                <h3>High Correlation Pairs (|r| > 0.7)</h3>
                <table>
                    <thead>
                        <tr><th>Feature 1</th><th>Feature 2</th><th>Correlation</th></tr>
                    </thead>
                    <tbody>
                        {% for pair in correlation.high_correlation_pairs %}
                        <tr>
                            <td>{{ pair.feature1 }}</td>
                            <td>{{ pair.feature2 }}</td>
                            <td>{{ "%.3f"|format(pair.correlation|float) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
            </div>
            {% endif %}
            
            {% if missing_values %}
            <div class="section">
                <h2>Missing Values Analysis</h2>
                <p>Total Missing: {{ missing_values.total_missing }} ({{ "%.2f"|format(missing_values.total_missing_percent|float) }}%)</p>
                <table>
                    <thead>
                        <tr><th>Column</th><th>Count</th><th>Percentage</th></tr>
                    </thead>
                    <tbody>
                        {% for col, info in missing_values.by_column.items() %}
                        <tr>
                            <td>{{ col }}</td>
                            <td>{{ info.count }}</td>
                            <td>{{ "%.2f"|format(info.percentage|float) }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </body>
        </html>
        """
        return template
    
    def _ml_report_template(self, data: Dict[str, Any]) -> str:
        """Generate a machine learning report template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #2E86AB; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; }
                .section { margin: 20px 0; }
                .metric { display: inline-block; margin: 10px; padding: 15px; 
                         background-color: #f9f9f9; border-radius: 5px; min-width: 200px; }
                .chart-container { margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>
            <p>Generated on: {{ timestamp }}</p>
            
            <div class="section">
                <h2>Model Information</h2>
                <div class="metric">Model Type: {{ model_info.type }}</div>
                <div class="metric">Problem Type: {{ model_info.problem_type }}</div>
                <div class="metric">Training Date: {{ model_info.training_date }}</div>
            </div>
            
            {% if model_metrics %}
            <div class="section">
                <h2>Model Performance Metrics</h2>
                {% for metric, value in model_metrics.items() %}
                <div class="metric">{{ metric|title }}: {{ "%.4f"|format(value|float) }}</div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if cross_validation %}
            <div class="section">
                <h2>Cross-Validation Results</h2>
                <div class="metric">Mean Score: {{ "%.4f"|format(cross_validation.cv_mean_score|float) }}</div>
                <div class="metric">Std Deviation: {{ "%.4f"|format(cross_validation.cv_std_score|float) }}</div>
            </div>
            {% endif %}
            
            {% if feature_importance %}
            <div class="section">
                <h2>Feature Importance</h2>
                <table>
                    <thead>
                        <tr><th>Feature</th><th>Importance</th></tr>
                    </thead>
                    <tbody>
                        {% for feature, importance in feature_importance|dictsort(by='value', reverse=True) %}
                        <tr>
                            <td>{{ feature }}</td>
                            <td>{{ "%.4f"|format(importance|float) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
            
            {% if training_details %}
            <div class="section">
                <h2>Training Details</h2>
                <ul>
                    <li>Training Samples: {{ training_details.train_samples }}</li>
                    <li>Test Samples: {{ training_details.test_samples }}</li>
                    <li>Features Used: {{ training_details.features_used }}</li>
                </ul>
            </div>
            {% endif %}
        </body>
        </html>
        """
        return template
    
    def _comparison_report_template(self, data: Dict[str, Any]) -> str:
        """Generate a model comparison report template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #2E86AB; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; }
                .section { margin: 20px 0; }
                .metric { display: inline-block; margin: 10px; padding: 15px; 
                         background-color: #f9f9f9; border-radius: 5px; min-width: 200px; }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>
            <p>Generated on: {{ timestamp }}</p>
            
            <div class="section">
                <h2>Model Comparison Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            {% for metric in comparison_results[list(comparison_results.keys())[0]].metrics.keys() %}
                            <th>{{ metric|title }}</th>
                            {% endfor %}
                            <th>CV Mean</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for model_name, results in comparison_results.items() %}
                        <tr>
                            <td>{{ model_name }}</td>
                            {% for metric, value in results.metrics.items() %}
                            <td>{{ "%.4f"|format(value|float) }}</td>
                            {% endfor %}
                            <td>{{ "%.4f"|format(results.cross_validation.cv_mean_score|float) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            {% if best_model %}
            <div class="section">
                <h2>Best Performing Model</h2>
                <div class="metric">Model: {{ best_model.name }}</div>
                <div class="metric">Metric: {{ best_model.metric }}</div>
                <div class="metric">Score: {{ "%.4f"|format(best_model.score|float) }}</div>
            </div>
            {% endif %}
        </body>
        </html>
        """
        return template
    
    def generate_basic_report(self, df: pd.DataFrame, title: str = "Data Report") -> str:
        """Generate a basic data report."""
        overview = {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage': round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
            'numeric_summary': df.describe().to_dict() if not df.select_dtypes(include=[np.number]).empty else {},
            'missing_values': df.isnull().sum().to_dict()
        }
        
        data = {
            'title': title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overview': overview
        }
        
        template_str = self._basic_report_template(data)
        template = Template(template_str)
        
        return template.render(data)
    
    def generate_eda_report(self, df: pd.DataFrame, title: str = "EDA Report") -> str:
        """Generate a comprehensive EDA report."""
        from .eda import eda_engine
        
        # Use the EDA engine to perform analysis
        eda_engine.load_data(df)
        profile = eda_engine.generate_profile_report()
        
        data = {
            'title': title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overview': profile['dataset_overview'],
            'distributions': profile['distributions'],
            'correlation': profile['correlation_analysis'],
            'missing_values': profile['missing_values_analysis']
        }
        
        template_str = self._eda_report_template(data)
        template = Template(template_str)
        
        return template.render(data)
    
    def generate_ml_report(self, model_info: Dict[str, Any], model_metrics: Dict[str, float],
                          cross_validation: Optional[Dict] = None, 
                          feature_importance: Optional[Dict[str, float]] = None,
                          training_details: Optional[Dict[str, Any]] = None,
                          title: str = "ML Model Report") -> str:
        """Generate a machine learning model report."""
        data = {
            'title': title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'model_info': model_info,
            'model_metrics': model_metrics,
            'cross_validation': cross_validation or {},
            'feature_importance': feature_importance or {},
            'training_details': training_details or {}
        }
        
        template_str = self._ml_report_template(data)
        template = Template(template_str)
        
        return template.render(data)
    
    def generate_comparison_report(self, comparison_results: Dict[str, Any],
                                 title: str = "Model Comparison Report") -> str:
        """Generate a model comparison report."""
        # Find the best performing model
        best_model = {'name': '', 'metric': '', 'score': 0}
        for model_name, results in comparison_results.items():
            for metric, score in results['metrics'].items():
                if score > best_model['score']:
                    best_model = {
                        'name': model_name,
                        'metric': metric,
                        'score': score
                    }
        
        data = {
            'title': title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'comparison_results': comparison_results,
            'best_model': best_model
        }
        
        template_str = self._comparison_report_template(data)
        template = Template(template_str)
        
        return template.render(data)
    
    def generate_comprehensive_report(self, df: pd.DataFrame, 
                                    report_types: List[str] = ['basic', 'eda'],
                                    title: str = "Comprehensive Data Report") -> str:
        """Generate a comprehensive report combining multiple report types."""
        combined_data = {
            'title': title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sections': {}
        }
        
        for report_type in report_types:
            if report_type == 'basic':
                combined_data['sections']['basic'] = {
                    'overview': {
                        'rows': len(df),
                        'columns': len(df.columns),
                        'memory_usage': round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
                        'numeric_summary': df.describe().to_dict() if not df.select_dtypes(include=[np.number]).empty else {},
                        'missing_values': df.isnull().sum().to_dict()
                    }
                }
            elif report_type == 'eda':
                from .eda import eda_engine
                eda_engine.load_data(df)
                profile = eda_engine.generate_profile_report()
                combined_data['sections']['eda'] = {
                    'overview': profile['dataset_overview'],
                    'distributions': profile['distributions'],
                    'correlation': profile['correlation_analysis'],
                    'missing_values': profile['missing_values_analysis']
                }
        
        # Create a comprehensive template
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #2E86AB; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; }
                .section { margin: 20px 0; padding: 15px; border-left: 4px solid #2E86AB; background-color: #f9f9f9; }
                .metric { display: inline-block; margin: 10px; padding: 15px; 
                         background-color: white; border-radius: 5px; min-width: 200px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>
            <p>Generated on: {{ timestamp }}</p>
            
            {% if sections.basic %}
            <div class="section">
                <h2>Basic Dataset Overview</h2>
                <div class="metric">Rows: {{ sections.basic.overview.rows }}</div>
                <div class="metric">Columns: {{ sections.basic.overview.columns }}</div>
                <div class="metric">Memory Usage: {{ sections.basic.overview.memory_usage }} MB</div>
                
                {% if sections.basic.overview.numeric_summary %}
                <h3>Numeric Columns Summary</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            {% for col in sections.basic.overview.numeric_summary.keys() %}
                            <th>{{ col }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for metric in sections.basic.overview.numeric_summary[list(sections.basic.overview.numeric_summary.keys())[0]].keys() %}
                        <tr>
                            <td>{{ metric }}</td>
                            {% for col in sections.basic.overview.numeric_summary.keys() %}
                            <td>{{ "%.2f"|format(sections.basic.overview.numeric_summary[col][metric]|float) }}</td>
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
                
                {% if sections.basic.overview.missing_values %}
                <h3>Missing Values</h3>
                <table>
                    <thead>
                        <tr><th>Column</th><th>Count</th><th>Percentage</th></tr>
                    </thead>
                    <tbody>
                        {% for col, count in sections.basic.overview.missing_values.items() %}
                        <tr>
                            <td>{{ col }}</td>
                            <td>{{ count }}</td>
                            <td>{{ "%.2f"|format((count / sections.basic.overview.rows * 100)|float) }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
            </div>
            {% endif %}
            
            {% if sections.eda %}
            <div class="section">
                <h2>Exploratory Data Analysis</h2>
                <div class="metric">Numeric Columns: {{ sections.eda.overview.numeric_columns }}</div>
                <div class="metric">Categorical Columns: {{ sections.eda.overview.categorical_columns }}</div>
                <div class="metric">Total Rows: {{ sections.eda.overview.total_rows }}</div>
                
                {% if sections.eda.correlation and sections.eda.correlation.high_correlation_pairs %}
                <h3>High Correlation Pairs</h3>
                <table>
                    <thead>
                        <tr><th>Feature 1</th><th>Feature 2</th><th>Correlation</th></tr>
                    </thead>
                    <tbody>
                        {% for pair in sections.eda.correlation.high_correlation_pairs %}
                        <tr>
                            <td>{{ pair.feature1 }}</td>
                            <td>{{ pair.feature2 }}</td>
                            <td>{{ "%.3f"|format(pair.correlation|float) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
                
                {% if sections.eda.missing_values %}
                <h3>Missing Values Analysis</h3>
                <p>Total Missing: {{ sections.eda.missing_values.total_missing }} ({{ "%.2f"|format(sections.eda.missing_values.total_missing_percent|float) }}%)</p>
                <table>
                    <thead>
                        <tr><th>Column</th><th>Count</th><th>Percentage</th></tr>
                    </thead>
                    <tbody>
                        {% for col, info in sections.eda.missing_values.by_column.items() %}
                        <tr>
                            <td>{{ col }}</td>
                            <td>{{ info.count }}</td>
                            <td>{{ "%.2f"|format(info.percentage|float) }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
            </div>
            {% endif %}
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(combined_data)
    
    def export_report(self, report_html: str, filename: str, format: str = 'html') -> str:
        """Export the report to a file."""
        filepath = f"{filename}.{format}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        return filepath
    
    def generate_pdf_report(self, report_html: str, filename: str) -> str:
        """Generate a PDF report from HTML."""
        try:
            from weasyprint import HTML
            import tempfile
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as temp_html:
                temp_html.write(report_html)
                temp_html_path = temp_html.name
            
            # Convert to PDF
            pdf_path = f"{filename}.pdf"
            HTML(temp_html_path).write_pdf(pdf_path)
            
            # Clean up temporary file
            os.unlink(temp_html_path)
            
            return pdf_path
        except ImportError:
            raise ImportError("weasyprint is required for PDF generation. Install with: pip install weasyprint")
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for the dataframe."""
        numeric_df = df.select_dtypes(include=[np.number])
        
        summary = {
            'dataset_info': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_columns': len(numeric_df.columns),
                'categorical_columns': len(df.select_dtypes(include=['object', 'category']).columns),
                'memory_usage_mb': round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
            }
        }
        
        if not numeric_df.empty:
            summary['numeric_summary'] = numeric_df.describe().to_dict()
        
        summary['missing_values'] = df.isnull().sum().to_dict()
        summary['duplicate_rows'] = int(df.duplicated().sum())
        
        return summary

# Global instance
report_generator = ReportGenerator()