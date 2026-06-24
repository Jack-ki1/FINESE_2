"""
FINESE2 - Consolidated Visualization Module
Comprehensive data visualization capabilities in a single module.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class Visualizer:
    """
    Consolidated visualization engine providing comprehensive plotting capabilities.
    """
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
        self.continuous_colorscale = px.colors.sequential.Viridis
    
    def create_chart(self, df: pd.DataFrame, chart_type: str, x_col: str = None, 
                     y_col: str = None, color_col: str = None, **kwargs) -> go.Figure:
        """Create a chart based on the specified type."""
        chart_methods = {
            'scatter': self.create_scatter_plot,
            'line': self.create_line_plot,
            'bar': self.create_bar_plot,
            'histogram': self.create_histogram,
            'box': self.create_box_plot,
            'heatmap': self.create_heatmap,
            'pie': self.create_pie_chart,
            'violin': self.create_violin_plot,
        }
        
        if chart_type not in chart_methods:
            raise ValueError(f"Unsupported chart type: {chart_type}. Supported types: {list(chart_methods.keys())}")
        
        # Call the appropriate chart method with provided parameters
        method = chart_methods[chart_type]
        
        # Build kwargs based on chart type requirements
        chart_kwargs = {'df': df, 'title': f"{chart_type.title()} Chart"}
        
        if x_col:
            chart_kwargs['x_col'] = x_col
        if y_col:
            chart_kwargs['y_col'] = y_col
        if color_col:
            chart_kwargs['color_col'] = color_col
        
        # Add any additional kwargs
        chart_kwargs.update(kwargs)
        
        return method(**chart_kwargs)
    
    def create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, 
                           color_col: str = None, size_col: str = None, 
                           title: str = "Scatter Plot", **kwargs) -> go.Figure:
        """Create a scatter plot with optional color and size encoding."""
        fig = px.scatter(
            df, 
            x=x_col, 
            y=y_col, 
            color=color_col,
            size=size_col,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            template="plotly_white",
            width=800,
            height=600
        )
        
        return fig
    
    def create_line_plot(self, df: pd.DataFrame, x_col: str, y_col: str, 
                        color_col: str = None, title: str = "Line Plot", 
                        **kwargs) -> go.Figure:
        """Create a line plot."""
        fig = px.line(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            template="plotly_white",
            width=800,
            height=600
        )
        
        return fig
    
    def create_bar_plot(self, df: pd.DataFrame, x_col: str, y_col: str = None,
                       color_col: str = None, orientation: str = 'v',
                       title: str = "Bar Plot", **kwargs) -> go.Figure:
        """Create a bar plot."""
        if y_col is None:
            # If y_col is not provided, count occurrences of x_col
            counts = df[x_col].value_counts().reset_index()
            counts.columns = [x_col, 'count']
            y_col = 'count'
        
        fig = px.bar(
            df if y_col != 'count' else counts,
            x=x_col,
            y=y_col,
            color=color_col,
            orientation=orientation,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            template="plotly_white",
            width=800,
            height=600
        )
        
        return fig
    
    def create_histogram(self, df: pd.DataFrame, x_col: str, 
                        color_col: str = None, nbins: int = None,
                        title: str = "Histogram", **kwargs) -> go.Figure:
        """Create a histogram."""
        fig = px.histogram(
            df,
            x=x_col,
            color=color_col,
            nbins=nbins,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            template="plotly_white",
            width=800,
            height=600
        )
        
        return fig
    
    def create_box_plot(self, df: pd.DataFrame, y_col: str, x_col: str = None,
                       color_col: str = None, title: str = "Box Plot", 
                       **kwargs) -> go.Figure:
        """Create a box plot."""
        fig = px.box(
            df,
            y=y_col,
            x=x_col,
            color=color_col,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            template="plotly_white",
            width=800,
            height=600
        )
        
        return fig
    
    def create_heatmap(self, df: pd.DataFrame, columns: List[str] = None,
                      title: str = "Correlation Heatmap", **kwargs) -> go.Figure:
        """Create a correlation heatmap."""
        if columns:
            corr_df = df[columns].corr()
        else:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            corr_df = df[numeric_cols].corr()
        
        fig = px.imshow(
            corr_df,
            text_auto=True,
            aspect="auto",
            title=title,
            color_continuous_scale=self.continuous_colorscale,
            **kwargs
        )
        
        fig.update_layout(
            width=800,
            height=600
        )
        
        return fig
    
    def create_pie_chart(self, df: pd.DataFrame, values_col: str, names_col: str,
                        title: str = "Pie Chart", **kwargs) -> go.Figure:
        """Create a pie chart."""
        fig = px.pie(
            df,
            values=values_col,
            names=names_col,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            width=800,
            height=600
        )
        
        return fig
    
    def create_violin_plot(self, df: pd.DataFrame, y_col: str, x_col: str = None,
                          color_col: str = None, title: str = "Violin Plot",
                          **kwargs) -> go.Figure:
        """Create a violin plot."""
        fig = px.violin(
            df,
            y=y_col,
            x=x_col,
            color=color_col,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            template="plotly_white",
            width=800,
            height=600
        )
        
        return fig
    
    def create_pair_plot(self, df: pd.DataFrame, columns: List[str],
                        title: str = "Pair Plot", **kwargs) -> go.Figure:
        """Create a pair plot (scatter matrix)."""
        fig = px.scatter_matrix(
            df[columns],
            dimensions=columns,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            title=title,
            width=min(1200, len(columns) * 300),
            height=min(1200, len(columns) * 300)
        )
        
        return fig
    
    def create_time_series(self, df: pd.DataFrame, date_col: str, value_col: str,
                          color_col: str = None, title: str = "Time Series",
                          **kwargs) -> go.Figure:
        """Create a time series plot."""
        # Convert date column to datetime if needed
        df_plot = df.copy()
        df_plot[date_col] = pd.to_datetime(df_plot[date_col])
        
        fig = px.line(
            df_plot,
            x=date_col,
            y=value_col,
            color=color_col,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            template="plotly_white",
            width=1000,
            height=600
        )
        
        return fig
    
    def create_radar_chart(self, df: pd.DataFrame, categories: List[str], 
                          values_col: str = None, group_col: str = None,
                          title: str = "Radar Chart") -> go.Figure:
        """Create a radar chart."""
        fig = go.Figure()
        
        if group_col:
            # Multiple groups
            for group in df[group_col].unique():
                group_data = df[df[group_col] == group]
                values = [group_data[cat].iloc[0] if cat in group_data.columns else 0 for cat in categories]
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=str(group)
                ))
        else:
            # Single group
            values = [df[cat].iloc[0] if cat in df.columns else 0 for cat in categories]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Data'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.1] if 'values' in locals() else [0, 1]
                )),
            showlegend=True,
            title=title
        )
        
        return fig
    
    def create_treemap(self, df: pd.DataFrame, path: List[str], values_col: str,
                      title: str = "Treemap", **kwargs) -> go.Figure:
        """Create a treemap."""
        fig = px.treemap(
            df,
            path=path,
            values=values_col,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            width=800,
            height=600
        )
        
        return fig
    
    def create_sunburst(self, df: pd.DataFrame, path: List[str], values_col: str,
                       title: str = "Sunburst Chart", **kwargs) -> go.Figure:
        """Create a sunburst chart."""
        fig = px.sunburst(
            df,
            path=path,
            values=values_col,
            title=title,
            color_discrete_sequence=self.color_palette,
            **kwargs
        )
        
        fig.update_layout(
            width=800,
            height=600
        )
        
        return fig
    
    def create_custom_dashboard(self, plots: List[Tuple[go.Figure, int, int]], 
                               title: str = "Dashboard") -> go.Figure:
        """Create a custom dashboard with multiple plots arranged in a grid."""
        # Calculate total rows and cols needed
        max_row = max(plot[1] for plot in plots) + 1
        max_col = max(plot[2] for plot in plots) + 1
        
        # Create subplots
        fig = make_subplots(
            rows=max_row, 
            cols=max_col,
            subplot_titles=[f"Plot {i+1}" for i in range(len(plots))]
        )
        
        for i, (plot_fig, row, col) in enumerate(plots):
            # Extract traces from the individual plot
            for trace in plot_fig.data:
                fig.add_trace(trace, row=row+1, col=col+1)
        
        fig.update_layout(
            title=title,
            height=300 * max_row,
            width=400 * max_col
        )
        
        return fig
    
    def create_statistical_summary_charts(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create a set of statistical summary charts."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        charts = {}
        
        # Distribution plots for numeric columns (first 4)
        for i, col in enumerate(numeric_cols[:4]):
            charts[f'dist_{col}'] = self.create_histogram(df, col, title=f'Distribution of {col}')
        
        # Bar charts for categorical columns (first 4)
        for i, col in enumerate(categorical_cols[:4]):
            value_counts = df[col].value_counts().reset_index()
            value_counts.columns = [col, 'count']
            charts[f'bar_{col}'] = self.create_bar_plot(value_counts, col, 'count', title=f'Distribution of {col}')
        
        # Correlation heatmap if we have numeric columns
        if len(numeric_cols) > 1:
            charts['correlation_heatmap'] = self.create_heatmap(df, numeric_cols[:10], title='Correlation Heatmap')
        
        return charts
    
    def export_figure(self, fig: go.Figure, filename: str, format: str = 'png'):
        """Export figure to file."""
        try:
            import kaleido
            fig.write_image(f"{filename}.{format}", format=format)
        except ImportError:
            # Fallback to HTML if kaleido is not available
            fig.write_html(f"{filename}.html")
    
    def generate_interactive_report(self, df: pd.DataFrame, title: str = "Data Visualization Report"):
        """Generate a comprehensive interactive report with multiple visualizations."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        report_charts = {}
        
        # Basic statistics visualizations
        if len(numeric_cols) >= 1:
            # Histogram for first numeric column
            report_charts['histogram'] = self.create_histogram(df, numeric_cols[0], 
                                                              title=f'Distribution of {numeric_cols[0]}')
            
            # Box plot for first numeric column
            report_charts['box_plot'] = self.create_box_plot(df, numeric_cols[0], 
                                                            title=f'Box Plot of {numeric_cols[0]}')
        
        if len(numeric_cols) >= 2:
            # Scatter plot for first two numeric columns
            report_charts['scatter'] = self.create_scatter_plot(df, numeric_cols[0], numeric_cols[1], 
                                                              title=f'{numeric_cols[0]} vs {numeric_cols[1]}')
        
        if len(categorical_cols) >= 1:
            # Bar chart for first categorical column
            value_counts = df[categorical_cols[0]].value_counts().head(10).reset_index()
            value_counts.columns = [categorical_cols[0], 'count']
            report_charts['bar_chart'] = self.create_bar_plot(value_counts, categorical_cols[0], 'count',
                                                             title=f'Top Categories in {categorical_cols[0]}')
        
        # Correlation heatmap if possible
        if len(numeric_cols) > 1:
            report_charts['correlation'] = self.create_heatmap(df, numeric_cols[:8], 
                                                              title='Feature Correlation Matrix')
        
        return report_charts

# Global visualizer instance
visualizer = Visualizer()