"""
Visualization Engine - Interactive Plotly-based charts
Refactored: No Streamlit dependencies
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


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
        frac = max_points / len(df)
        return df.sample(frac=frac, random_state=42)

    @classmethod
    def bar_chart(cls, df: pd.DataFrame, x: str, y: str, color: Optional[str] = None,
                  title: str = "", orientation: str = "v", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive bar chart."""
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
        """Create interactive line chart."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        fig = px.line(sampled_df, x=x, y=y, color=color, title=title,
                     color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(line=dict(width=3))
        return cls._apply_theme(fig)

    @classmethod
    def scatter_plot(cls, df: pd.DataFrame, x: str, y: str, color: Optional[str] = None,
                     size: Optional[str] = None, title: str = "", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive scatter plot."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        fig = px.scatter(sampled_df, x=x, y=y, color=color, size=size, title=title,
                        color_discrete_sequence=cls.DEFAULT_COLORS, opacity=0.7, **kwargs)
        fig.update_traces(marker=dict(line=dict(width=1, color='#2D2D2D')))
        return cls._apply_theme(fig)

    @classmethod
    def histogram(cls, df: pd.DataFrame, x: str, color: Optional[str] = None,
                  title: str = "", nbins: int = 50, max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive histogram."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        fig = px.histogram(sampled_df, x=x, color=color, title=title, nbinsx=nbins,
                          color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(marker_line_color='#2D2D2D', marker_line_width=1)
        return cls._apply_theme(fig)

    @classmethod
    def box_plot(cls, df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None,
                 color: Optional[str] = None, title: str = "", max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive box plot."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        fig = px.box(sampled_df, x=x, y=y, color=color, title=title,
                    color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        return cls._apply_theme(fig)

    @classmethod
    def pie_chart(cls, df: pd.DataFrame, names: str, values: str, title: str = "",
                  max_points: int = 10000, **kwargs) -> go.Figure:
        """Create interactive pie chart."""
        sampled_df = cls._sample_data_for_viz(df, max_points)
        fig = px.pie(sampled_df, names=names, values=values, title=title,
                    color_discrete_sequence=cls.DEFAULT_COLORS, **kwargs)
        fig.update_traces(textposition='inside', textinfo='percent+label',
                         hole=0.4, marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2))
        return cls._apply_theme(fig)

    @classmethod
    def heatmap(cls, df: pd.DataFrame, x: str = None, y: str = None, z: str = None,
                title: str = "Heatmap", **kwargs) -> go.Figure:
        """Create heatmap from dataframe."""
        if x and y and z:
            # Pivot-based heatmap
            pivot = df.pivot_table(index=y, columns=x, values=z, aggfunc='mean')
            fig = px.imshow(pivot, title=title, color_continuous_scale=["#FFFFFF", "#00D4AA"], **kwargs)
        else:
            fig = px.imshow(df.select_dtypes(include=[np.number]), title=title,
                          color_continuous_scale=["#FFFFFF", "#00D4AA"], **kwargs)
        fig.update_layout(coloraxis_colorbar=dict(title=""))
        return cls._apply_theme(fig)

    @classmethod
    def dashboard_summary(cls, df: pd.DataFrame, max_points: int = 5000) -> Dict[str, go.Figure]:
        """Generate a quick dashboard with key visualizations."""
        charts = {}
        sampled_df = cls._sample_data_for_viz(df, max_points)

        numeric_cols = sampled_df.select_dtypes(include=[np.number]).columns[:4]
        if len(numeric_cols) > 0:
            fig = make_subplots(rows=2, cols=2, subplot_titles=list(numeric_cols[:4]))
            for i, col in enumerate(numeric_cols[:4]):
                row = i // 2 + 1
                col_idx = i % 2 + 1
                fig.add_trace(go.Histogram(x=sampled_df[col].dropna(), name=col,
                                          marker_color=cls.DEFAULT_COLORS[i]), row=row, col=col_idx)
            fig.update_layout(height=600, showlegend=False, title_text="Numeric Distributions")
            charts["distributions"] = cls._apply_theme(fig)

        cat_cols = sampled_df.select_dtypes(include=['object', 'category']).columns[:2]
        if len(cat_cols) > 0:
            for col in cat_cols:
                counts = sampled_df[col].value_counts().head(10).reset_index()
                counts.columns = [col, 'count']
                charts[f"{col}_breakdown"] = cls.bar_chart(counts, x=col, y='count',
                                                          title=f"Top {col} Values")

        return charts
