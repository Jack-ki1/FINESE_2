"""
Visualization Engine - Interactive Plotly-based charts
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

class Visualizer:
    """Create interactive, publication-ready visualizations."""

    DEFAULT_COLORS = ["#00D4AA", "#6C63FF", "#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF", "#FF9F45", "#C9B1FF"]

    @classmethod
    def _apply_theme(cls, fig: go.Figure) -> go.Figure:
        """Apply standard Plotly styling to figure."""
        fig.update_layout(
            template="plotly_white",
            font=dict(family="Inter, sans-serif", color="#2D2D2D"),
            title_font=dict(size=18, color="#2D2D2D"),
            legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#CCCCCC", borderwidth=1),
            margin=dict(l=60, r=40, t=80, b=60)
        )
        return fig

    @classmethod
    def _sample_data_for_viz(cls, df: pd.DataFrame, max_points: int = 10000) -> pd.DataFrame:
        """Sample data if it exceeds max_points for better performance."""
        if len(df) <= max_points:
            return df
        else:
            # Calculate sampling fraction
            frac = max_points / len(df)
            return df.sample(frac=frac, random_state=42)

    @classmethod
    def bar_chart(cls, df: pd.DataFrame, x: str, y: str, color: Optional[str] = None,
                  title: str = "", orientation: str = "v", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive bar chart with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        if orientation == "h":
            fig = px.bar(sampled_df, y=x, x=y, color=color, title=title, 
                        color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        else:
            fig = px.bar(sampled_df, x=x, y=y, color=color, title=title,
                        color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        return cls._apply_theme(fig)

    @classmethod
    def line_chart(cls, df: pd.DataFrame, x: str, y: str, color: Optional[str] = None,
                   title: str = "", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive line chart with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.line(sampled_df, x=x, y=y, color=color, title=title,
                     color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(line=dict(width=3))
        return cls._apply_theme(fig)

    @classmethod
    def scatter_plot(cls, df: pd.DataFrame, x: str, y: str, color: Optional[str] = None,
                     size: Optional[str] = None, title: str = "", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive scatter plot with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.scatter(sampled_df, x=x, y=y, color=color, size=size, title=title,
                        color_discrete_sequence=cls.DEFAULT_COLORS,
                        opacity=0.7, **kwargs)
        fig.update_traces(marker=dict(line=dict(width=1, color='#2D2D2D')))
        return cls._apply_theme(fig)

    @classmethod
    def histogram(cls, df: pd.DataFrame, x: str, color: Optional[str] = None,
                  title: str = "", bins: int = 50, max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive histogram with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.histogram(sampled_df, x=x, color=color, title=title, nbins=bins,
                          color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(marker_line_color='#2D2D2D', marker_line_width=1)
        return cls._apply_theme(fig)

    @classmethod
    def box_plot(cls, df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None,
                 color: Optional[str] = None, title: str = "", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive box plot with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.box(sampled_df, x=x, y=y, color=color, title=title,
                    color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        return cls._apply_theme(fig)

    @classmethod
    def violin_plot(cls, df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None,
                    color: Optional[str] = None, title: str = "", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive violin plot with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.violin(sampled_df, x=x, y=y, color=color, title=title, box=True,
                       color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        return cls._apply_theme(fig)

    @classmethod
    def pie_chart(cls, df: pd.DataFrame, names: str, values: str, title: str = "", 
                  max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive pie chart with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.pie(sampled_df, names=names, values=values, title=title,
                    color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(textposition='inside', textinfo='percent+label',
                         hole=0.4, marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2))
        return cls._apply_theme(fig)

    @classmethod
    def heatmap(cls, df: pd.DataFrame, title: str = "Heatmap", **kwargs) -> go.Figure:
        """Create heatmap from dataframe."""
        # For heatmaps, we don't sample the data since it's typically aggregated
        fig = px.imshow(df, title=title, color_continuous_scale=["#FFFFFF", "#00D4AA"], **kwargs)
        fig.update_layout(coloraxis_colorbar=dict(title=""))
        return cls._apply_theme(fig)

    @classmethod
    def treemap(cls, df: pd.DataFrame, path: List[str], values: str, title: str = "", 
                max_points: int = 10000, **kwargs) -> go.Figure:
        """Create treemap with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.treemap(sampled_df, path=path, values=values, title=title,
                        color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(textinfo="label+value+percent parent",
                         marker=dict(line=dict(color='#FFFFFF', width=2)))
        return cls._apply_theme(fig)

    @classmethod
    def sunburst(cls, df: pd.DataFrame, path: List[str], values: str, title: str = "", 
                 max_points: int = 10000, **kwargs) -> go.Figure:
        """Create sunburst chart with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.sunburst(sampled_df, path=path, values=values, title=title,
                         color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(textinfo="label+percent parent")
        return cls._apply_theme(fig)

    @classmethod
    def area_chart(cls, df: pd.DataFrame, x: str, y: str, color: Optional[str] = None,
                   title: str = "", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create stacked area chart with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.area(sampled_df, x=x, y=y, color=color, title=title,
                     color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(line=dict(width=0))
        return cls._apply_theme(fig)

    @classmethod
    def funnel_chart(cls, df: pd.DataFrame, x: str, y: str, title: str = "", 
                     max_points: int = 10000, **kwargs) -> go.Figure:
        """Create funnel chart with sampling for large datasets."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        fig = px.funnel(sampled_df, x=x, y=y, title=title,
                       color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        return cls._apply_theme(fig)

    @classmethod
    def waterfall_chart(cls, categories: List[str], values: List[float], title: str = "") -> go.Figure:
        """Create waterfall chart."""
        fig = go.Figure(go.Waterfall(
            name="Waterfall",
            orientation="v",
            measure=["relative"] * len(values),
            x=categories,
            y=values,
            connector={"line": {"color": "#CCCCCC"}},
            decreasing={"marker": {"color": "#E74C3C"}},
            increasing={"marker": {"color": "#00D4AA"}},
            totals={"marker": {"color": "#6C63FF"}}
        ))
        fig.update_layout(title=title)
        return cls._apply_theme(fig)

    @classmethod
    def gauge_chart(cls, value: float, min_val: float = 0, max_val: float = 100, title: str = "") -> go.Figure:
        """Create gauge chart."""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': "#00D4AA"},
                'steps': [
                    {'range': [min_val, (max_val-min_val)*0.5 + min_val], 'color': "#E74C3C"},
                    {'range': [(max_val-min_val)*0.5 + min_val, (max_val-min_val)*0.8 + min_val], 'color': "#F39C12"},
                    {'range': [(max_val-min_val)*0.8 + min_val, max_val], 'color': "#27AE60"}
                ],
                'threshold': {
                    'line': {'color': "#6C63FF", 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        return cls._apply_theme(fig)

    @classmethod
    def radar_chart(cls, df: pd.DataFrame, vars: List[str], title: str = "", 
                   max_points: int = 10000) -> go.Figure:
        """Create radar chart."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        # Calculate mean for each variable
        means = [sampled_df[var].mean() for var in vars]
        
        fig = go.Figure(go.Scatterpolar(
            r=means,
            theta=vars,
            fill='toself',
            name='Average'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(means) * 1.1 if means else 100]
                )),
            title=title
        )
        return cls._apply_theme(fig)

    @classmethod
    def correlation_heatmap(cls, df: pd.DataFrame, method: str = "pearson", 
                           title: str = "Correlation Heatmap", max_points: int = 10000) -> go.Figure:
        """Create correlation heatmap."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        # Calculate correlation matrix
        corr_matrix = sampled_df.corr(method=method)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Features",
            yaxis_title="Features"
        )
        
        return cls._apply_theme(fig)

    @classmethod
    def dashboard_summary(cls, df: pd.DataFrame, max_points: int = 5000) -> Dict[str, go.Figure]:
        """Generate a quick dashboard with key visualizations."""
        charts = {}

        # Sample data for dashboard if needed
        sampled_df = cls._sample_data_for_viz(df, max_points)
        
        # Numeric distributions
        numeric_cols = sampled_df.select_dtypes(include=[np.number]).columns[:4]
        if len(numeric_cols) > 0:
            fig = make_subplots(rows=2, cols=2, subplot_titles=numeric_cols[:4])
            for i, col in enumerate(numeric_cols[:4]):
                row = i // 2 + 1
                col_idx = i % 2 + 1
                fig.add_trace(go.Histogram(x=sampled_df[col].dropna(), name=col, 
                                          marker_color=cls.DEFAULT_COLORS[i]), row=row, col=col_idx)
            fig.update_layout(height=600, showlegend=False, title_text="Numeric Distributions")
            charts["distributions"] = cls._apply_theme(fig)

        # Categorical breakdowns
        cat_cols = sampled_df.select_dtypes(include=['object', 'category']).columns[:2]
        if len(cat_cols) > 0:
            for col in cat_cols:
                counts = sampled_df[col].value_counts().head(10).reset_index()
                counts.columns = [col, 'count']
                charts[f"{col}_breakdown"] = cls.bar_chart(counts, x=col, y='count', 
                                                          title=f"Top {col} Values")

        return charts