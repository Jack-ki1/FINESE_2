"""Chart Service Module - Handles visualization and chart creation functionality."""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, List, Optional, Tuple
from utils.data_utils import is_numeric_column, is_categorical_column, is_datetime_column

logger = logging.getLogger(__name__)

# Define constants for maximum data sizes to handle
MAX_ROWS_FOR_PLOT = 10000
MAX_COLS_FOR_HEATMAP = 50

def create_completeness_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing completeness percentage for each column.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Plotly figure object
    """
    # Limit data for performance
    if len(df) > MAX_ROWS_FOR_PLOT:
        sample_df = df.sample(n=MAX_ROWS_FOR_PLOT)
        logger.info(f"Downsampling data from {len(df)} to {MAX_ROWS_FOR_PLOT} rows for completeness chart")
    else:
        sample_df = df

    completeness = (1 - sample_df.isnull().sum() / len(sample_df)) * 100
    
    fig = px.bar(
        x=completeness.index, 
        y=completeness.values,
        labels={'x': 'Columns', 'y': 'Completeness (%)'},
        title="Column Completeness (%)",
        color=completeness.values, 
        color_continuous_scale='RdYlGn', 
        range_color=[0, 100]
    )
    fig.update_layout(
        yaxis_range=[0, 100],
        autosize=True,
        height=None,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def create_missing_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap showing missing values pattern.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Plotly figure object
    """
    # Downsample both rows and columns for performance
    if len(df) > MAX_ROWS_FOR_PLOT:
        sample_df = df.sample(n=MAX_ROWS_FOR_PLOT)
        logger.info(f"Downsampling data from {len(df)} to {MAX_ROWS_FOR_PLOT} rows for missing heatmap")
    else:
        sample_df = df
        
    if len(df.columns) > MAX_COLS_FOR_HEATMAP:
        sample_cols = df.columns[:MAX_COLS_FOR_HEATMAP]
        sample_df = sample_df[sample_cols]
        logger.info(f"Reducing columns from {len(df.columns)} to {MAX_COLS_FOR_HEATMAP} for missing heatmap")
    
    missing_matrix = sample_df.isnull().astype(int)
    
    fig = px.imshow(
        missing_matrix.T, 
        labels=dict(x="Rows", y="Columns", color="Missing"),
        title="Missing Values Heatmap (Yellow = Missing)", 
        color_continuous_scale='Viridis'
    )
    fig.update_layout(
        autosize=True,
        height=None,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def create_outlier_analysis(df: pd.DataFrame, selected_col: str) -> Tuple[Dict, go.Figure]:
    """
    Perform outlier analysis on a selected column.
    
    Args:
        df: Input DataFrame
        selected_col: Column to analyze
        
    Returns:
        Tuple of (outlier_stats_dict, plotly_figure)
    """
    if not is_numeric_column(df[selected_col]):
        raise ValueError(f"Column {selected_col} is not numeric")
    
    # Limit data for performance
    if len(df) > MAX_ROWS_FOR_PLOT:
        sample_df = df.sample(n=MAX_ROWS_FOR_PLOT)
        logger.info(f"Downsampling data from {len(df)} to {MAX_ROWS_FOR_PLOT} rows for outlier analysis")
    else:
        sample_df = df
    
    Q1 = sample_df[selected_col].quantile(0.25)
    Q3 = sample_df[selected_col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = sample_df[(sample_df[selected_col] < lower_bound) | (sample_df[selected_col] > upper_bound)]
    
    outlier_stats = {
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": len(outliers),
        "outlier_percentage": (len(outliers) / len(sample_df)) * 100
    }
    
    fig = px.box(sample_df, y=selected_col, title=f"Box Plot: {selected_col}")
    fig.add_hline(y=lower_bound, line_dash="dash", line_color="red", 
                  annotation_text=f"Lower bound: {lower_bound:.2f}")
    fig.add_hline(y=upper_bound, line_dash="dash", line_color="red", 
                  annotation_text=f"Upper bound: {upper_bound:.2f}")
    fig.update_layout(
        autosize=True, 
        height=None, 
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return outlier_stats, fig


def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create a correlation heatmap for numeric columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Plotly figure object
    """
    # Get numeric columns
    num_cols = [col for col in df.columns if is_numeric_column(df[col])]
    
    if len(num_cols) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Need at least 2 numeric columns for correlation analysis.",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Downsample for performance if too many columns
    if len(num_cols) > MAX_COLS_FOR_HEATMAP:
        num_cols = num_cols[:MAX_COLS_FOR_HEATMAP]
        logger.info(f"Limited correlation analysis to {MAX_COLS_FOR_HEATMAP} columns")
    
    # Limit rows for performance
    sample_df = df
    if len(df) > MAX_ROWS_FOR_PLOT:
        sample_df = df.sample(n=MAX_ROWS_FOR_PLOT)
        logger.info(f"Downsampling data from {len(df)} to {MAX_ROWS_FOR_PLOT} rows for correlation heatmap")
    
    corr = sample_df[num_cols].corr(numeric_only=True)
    
    fig = px.imshow(
        corr, 
        title="Correlation Heatmap", 
        color_continuous_scale='RdBu_r', 
        zmin=-1, 
        zmax=1,
        text_auto='.2f'
    )
    fig.update_layout(
        autosize=True, 
        height=None, 
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig


def create_distribution_plots(df: pd.DataFrame) -> List[go.Figure]:
    """
    Create distribution plots for numeric and categorical columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of plotly figure objects
    """
    figures = []
    
    # Sample data for performance
    if len(df) > MAX_ROWS_FOR_PLOT:
        sample_df = df.sample(n=MAX_ROWS_FOR_PLOT)
        logger.info(f"Downsampling data from {len(df)} to {MAX_ROWS_FOR_PLOT} rows for distribution plots")
    else:
        sample_df = df
    
    # Get numeric columns (limit to 3 for performance)
    num_cols = [col for col in df.columns if is_numeric_column(sample_df[col])][:3]
    
    for col in num_cols:
        fig = px.histogram(
            sample_df, 
            x=col, 
            nbins=30, 
            title=f"Distribution: {col}", 
            marginal="box"
        )
        fig.update_layout(
            autosize=True, 
            height=None, 
            margin=dict(l=20, r=20, t=60, b=20)
        )
        figures.append(fig)
    
    # Get categorical columns (limit to 3 for performance)
    cat_cols = [col for col in df.columns if is_categorical_column(sample_df[col])][:3]
    
    for col in cat_cols:
        # Get top 10 most frequent values for performance
        vc = sample_df[col].astype(str).value_counts(dropna=False).head(10)
        fig = px.bar(
            x=vc.index, 
            y=vc.values, 
            title=f"Distribution: {col}",
            labels={'x': col, 'y': 'Count'}
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            autosize=True, 
            height=None, 
            margin=dict(l=20, r=20, t=60, b=20)
        )
        figures.append(fig)
    
    return figures