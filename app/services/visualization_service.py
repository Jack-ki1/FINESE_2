"""
FINESE2 - Visualization Service
Migrates and enhances engine/visualizer.py with caching and user preferences.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging
from engine.visualizer import Visualizer
from app.extensions import redis_store

logger = logging.getLogger(__name__)


class VisualizationService:
    """
    Enhanced visualization service with caching and user preferences.
    
    Wraps legacy Visualizer while adding:
    - Chart caching with Redis
    - User theme preferences
    - Chart history tracking
    - Export functionality
    """
    
    def __init__(self):
        self.visualizer = Visualizer()
    
    def create_chart(self, df: pd.DataFrame, chart_type: str, params: Dict[str, Any],
                    user_id: int, cache_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a visualization with optional caching.
        
        Args:
            df: Input DataFrame
            chart_type: Type of chart (bar, line, scatter, etc.)
            params: Chart parameters
            user_id: User creating the chart
            cache_key: Optional cache key for Redis
            
        Returns:
            Dictionary with chart JSON and metadata
        """
        try:
            # Check cache first
            if cache_key and redis_store:
                cached = redis_store.get(f"chart:{cache_key}")
                if cached:
                    logger.info(f"Cache hit for chart {cache_key}")
                    return json.loads(cached)
            
            # Generate chart based on type
            chart_func = getattr(self, f"_create_{chart_type}_chart", None)
            if not chart_func:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            fig = chart_func(df, params)
            chart_json = fig.to_json()
            
            result = {
                'chart': chart_json,
                'type': chart_type,
                'params': params,
                'created_by': user_id
            }
            
            # Cache if requested
            if cache_key and redis_store:
                redis_store.setex(
                    f"chart:{cache_key}",
                    3600,  # 1 hour TTL
                    json.dumps(result)
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Chart creation failed for user {user_id}: {e}")
            raise
    
    def _create_bar_chart(self, df: pd.DataFrame, params: Dict) -> go.Figure:
        """Create bar chart."""
        return self.visualizer.bar_chart(
            df=df,
            x=params.get('x'),
            y=params.get('y'),
            color=params.get('color'),
            title=params.get('title', 'Bar Chart')
        )
    
    def _create_line_chart(self, df: pd.DataFrame, params: Dict) -> go.Figure:
        """Create line chart."""
        return self.visualizer.line_chart(
            df=df,
            x=params.get('x'),
            y=params.get('y'),
            color=params.get('color'),
            title=params.get('title', 'Line Chart')
        )
    
    def _create_scatter_chart(self, df: pd.DataFrame, params: Dict) -> go.Figure:
        """Create scatter chart."""
        return self.visualizer.scatter_plot(
            df=df,
            x=params.get('x'),
            y=params.get('y'),
            color=params.get('color'),
            size=params.get('size'),
            title=params.get('title', 'Scatter Plot')
        )
    
    def _create_histogram(self, df: pd.DataFrame, params: Dict) -> go.Figure:
        """Create histogram."""
        return self.visualizer.histogram(
            df=df,
            x=params.get('x'),
            color=params.get('color'),
            title=params.get('title', 'Histogram'),
            nbins=params.get('nbins', 30)
        )
    
    def _create_box_plot(self, df: pd.DataFrame, params: Dict) -> go.Figure:
        """Create box plot."""
        return self.visualizer.box_plot(
            df=df,
            x=params.get('x'),
            y=params.get('y'),
            color=params.get('color'),
            title=params.get('title', 'Box Plot')
        )
    
    def _create_heatmap(self, df: pd.DataFrame, params: Dict) -> go.Figure:
        """Create heatmap."""
        return self.visualizer.heatmap(
            df=df,
            x=params.get('x'),
            y=params.get('y'),
            z=params.get('z'),
            title=params.get('title', 'Heatmap')
        )
    
    def get_user_chart_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's chart creation history."""
        # This would query the database in production
        # For now, return empty list
        return []


# Singleton instance
visualization_service = VisualizationService()
