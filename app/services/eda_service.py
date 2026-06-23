"""
FINESE2 - EDA Service
Migrates and enhances engine/eda_engine.py with caching and user isolation.
"""
import io
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging
import traceback
from app.extensions import redis_store
from engine.eda_engine import EDAEngine

logger = logging.getLogger(__name__)


class EDASer:
    """
    EDA Service providing exploratory data analysis with caching and user isolation.
    
    This service wraps the EDAEngine functionality with Redis-based caching and 
    per-user data isolation for the FINESE2 application.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize EDA service for a specific user.
        
        Args:
            user_id (str): Unique identifier for the user
        """
        self.user_id = user_id
        self.engine = EDAEngine()
        self.cache_prefix = f"eda:user:{user_id}"
    
    def _get_cache_key(self, operation: str, params: Dict = None) -> str:
        """
        Generate a cache key for a specific operation and parameters.
        
        Args:
            operation (str): The operation name
            params (Dict, optional): Parameters to include in the key
            
        Returns:
            str: Generated cache key
        """
        key = f"{self.cache_prefix}:{operation}"
        if params:
            # Create a deterministic string from params for consistent hashing
            sorted_params = sorted((k, v) for k, v in params.items() if k != 'data')
            param_str = json.dumps(sorted_params, sort_keys=True)
            key += f":{hash(param_str)}"
        return key
    
    def analyze_dataset(self, data: pd.DataFrame, cache: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive dataset analysis with caching.
        
        Args:
            data (pd.DataFrame): Input dataset
            cache (bool): Whether to use caching
            
        Returns:
            Dict[str, Any]: Analysis results including metadata, statistics, and insights
        """
        try:
            cache_key = self._get_cache_key("analyze", {"shape": data.shape})
            
            if cache:
                cached_result = redis_store.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit for dataset analysis: {cache_key}")
                    return json.loads(cached_result)
            
            result = self.engine.analyze_dataset(data)
            
            if cache:
                redis_store.setex(
                    cache_key, 
                    3600,  # Cache for 1 hour
                    json.dumps(result, default=str)
                )
                logger.debug(f"Dataset analysis cached: {cache_key}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing dataset: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def generate_histogram(self, data: pd.DataFrame, column: str, 
                          bins: int = 30, cache: bool = True) -> str:
        """
        Generate histogram plot for a specified column.
        
        Args:
            data (pd.DataFrame): Input dataset
            column (str): Column name to plot
            bins (int): Number of bins for the histogram
            cache (bool): Whether to use caching
            
        Returns:
            str: Plotly JSON representation of the histogram
        """
        try:
            cache_key = self._get_cache_key("histogram", {"column": column, "bins": bins})
            
            if cache:
                cached_plot = redis_store.get(cache_key)
                if cached_plot:
                    logger.debug(f"Cache hit for histogram: {cache_key}")
                    return cached_plot.decode('utf-8')
            
            fig = self.engine.generate_histogram(data, column, bins)
            plot_json = fig.to_json()
            
            if cache:
                redis_store.setex(
                    cache_key,
                    1800,  # Cache for 30 minutes
                    plot_json.encode('utf-8')
                )
                logger.debug(f"Histogram cached: {cache_key}")
                
            return plot_json
            
        except Exception as e:
            logger.error(f"Error generating histogram for column {column}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def generate_scatter_plot(self, data: pd.DataFrame, x_col: str, y_col: str,
                             color_col: Optional[str] = None, cache: bool = True) -> str:
        """
        Generate scatter plot for two variables.
        
        Args:
            data (pd.DataFrame): Input dataset
            x_col (str): Column name for x-axis
            y_col (str): Column name for y-axis
            color_col (Optional[str]): Column name for color encoding
            cache (bool): Whether to use caching
            
        Returns:
            str: Plotly JSON representation of the scatter plot
        """
        try:
            cache_key = self._get_cache_key("scatter", {
                "x": x_col, "y": y_col, "color": color_col
            })
            
            if cache:
                cached_plot = redis_store.get(cache_key)
                if cached_plot:
                    logger.debug(f"Cache hit for scatter plot: {cache_key}")
                    return cached_plot.decode('utf-8')
            
            fig = self.engine.generate_scatter_plot(data, x_col, y_col, color_col)
            plot_json = fig.to_json()
            
            if cache:
                redis_store.setex(
                    cache_key,
                    1800,  # Cache for 30 minutes
                    plot_json.encode('utf-8')
                )
                logger.debug(f"Scatter plot cached: {cache_key}")
                
            return plot_json
            
        except Exception as e:
            logger.error(f"Error generating scatter plot ({x_col} vs {y_col}): {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def generate_correlation_heatmap(self, data: pd.DataFrame, 
                                    method: str = 'pearson', cache: bool = True) -> str:
        """
        Generate correlation heatmap for numerical columns.
        
        Args:
            data (pd.DataFrame): Input dataset
            method (str): Correlation method ('pearson', 'spearman', 'kendall')
            cache (bool): Whether to use caching
            
        Returns:
            str: Plotly JSON representation of the correlation heatmap
        """
        try:
            cache_key = self._get_cache_key("correlation", {"method": method})
            
            if cache:
                cached_plot = redis_store.get(cache_key)
                if cached_plot:
                    logger.debug(f"Cache hit for correlation heatmap: {cache_key}")
                    return cached_plot.decode('utf-8')
            
            fig = self.engine.generate_correlation_heatmap(data, method)
            plot_json = fig.to_json()
            
            if cache:
                redis_store.setex(
                    cache_key,
                    1800,  # Cache for 30 minutes
                    plot_json.encode('utf-8')
                )
                logger.debug(f"Correlation heatmap cached: {cache_key}")
                
            return plot_json
            
        except Exception as e:
            logger.error(f"Error generating correlation heatmap: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def get_column_statistics(self, data: pd.DataFrame, column: str, 
                             cache: bool = True) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific column.
        
        Args:
            data (pd.DataFrame): Input dataset
            column (str): Column name to analyze
            cache (bool): Whether to use caching
            
        Returns:
            Dict[str, Any]: Statistics including mean, median, mode, std, quantiles, etc.
        """
        try:
            cache_key = self._get_cache_key("column_stats", {"column": column})
            
            if cache:
                cached_stats = redis_store.get(cache_key)
                if cached_stats:
                    logger.debug(f"Cache hit for column statistics: {cache_key}")
                    return json.loads(cached_stats)
            
            stats = self.engine.get_column_statistics(data, column)
            
            if cache:
                redis_store.setex(
                    cache_key,
                    3600,  # Cache for 1 hour
                    json.dumps(stats, default=str)
                )
                logger.debug(f"Column statistics cached: {cache_key}")
                
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics for column {column}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def detect_outliers(self, data: pd.DataFrame, column: str, method: str = 'iqr',
                       cache: bool = True) -> Dict[str, Any]:
        """
        Detect outliers in a specified column.
        
        Args:
            data (pd.DataFrame): Input dataset
            column (str): Column name to check for outliers
            method (str): Method to use ('iqr', 'zscore')
            cache (bool): Whether to use caching
            
        Returns:
            Dict[str, Any]: Outlier detection results including threshold values and outlier indices
        """
        try:
            cache_key = self._get_cache_key("outliers", {"column": column, "method": method})
            
            if cache:
                cached_outliers = redis_store.get(cache_key)
                if cached_outliers:
                    logger.debug(f"Cache hit for outlier detection: {cache_key}")
                    return json.loads(cached_outliers)
            
            outliers = self.engine.detect_outliers(data, column, method)
            
            if cache:
                redis_store.setex(
                    cache_key,
                    3600,  # Cache for 1 hour
                    json.dumps(outliers, default=str)
                )
                logger.debug(f"Outlier detection cached: {cache_key}")
                
            return outliers
            
        except Exception as e:
            logger.error(f"Error detecting outliers in column {column}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def generate_box_plot(self, data: pd.DataFrame, column: str, 
                         group_by: Optional[str] = None, cache: bool = True) -> str:
        """
        Generate box plot for a specified column.
        
        Args:
            data (pd.DataFrame): Input dataset
            column (str): Column name to plot
            group_by (Optional[str]): Column name to group by for comparative box plots
            cache (bool): Whether to use caching
            
        Returns:
            str: Plotly JSON representation of the box plot
        """
        try:
            cache_key = self._get_cache_key("box_plot", {
                "column": column, "group_by": group_by
            })
            
            if cache:
                cached_plot = redis_store.get(cache_key)
                if cached_plot:
                    logger.debug(f"Cache hit for box plot: {cache_key}")
                    return cached_plot.decode('utf-8')
            
            fig = self.engine.generate_box_plot(data, column, group_by)
            plot_json = fig.to_json()
            
            if cache:
                redis_store.setex(
                    cache_key,
                    1800,  # Cache for 30 minutes
                    plot_json.encode('utf-8')
                )
                logger.debug(f"Box plot cached: {cache_key}")
                
            return plot_json
            
        except Exception as e:
            logger.error(f"Error generating box plot for column {column}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def generate_qq_plot(self, data: pd.DataFrame, column: str, cache: bool = True) -> str:
        """
        Generate Q-Q plot to assess normality of a distribution.
        
        Args:
            data (pd.DataFrame): Input dataset
            column (str): Column name to plot
            cache (bool): Whether to use caching
            
        Returns:
            str: Plotly JSON representation of the Q-Q plot
        """
        try:
            cache_key = self._get_cache_key("qq_plot", {"column": column})
            
            if cache:
                cached_plot = redis_store.get(cache_key)
                if cached_plot:
                    logger.debug(f"Cache hit for Q-Q plot: {cache_key}")
                    return cached_plot.decode('utf-8')
            
            fig = self.engine.generate_qq_plot(data, column)
            plot_json = fig.to_json()
            
            if cache:
                redis_store.setex(
                    cache_key,
                    1800,  # Cache for 30 minutes
                    plot_json.encode('utf-8')
                )
                logger.debug(f"Q-Q plot cached: {cache_key}")
                
            return plot_json
            
        except Exception as e:
            logger.error(f"Error generating Q-Q plot for column {column}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def detect_missing_values(self, data: pd.DataFrame, cache: bool = True) -> Dict[str, Any]:
        """
        Detect and analyze missing values in the dataset.
        
        Args:
            data (pd.DataFrame): Input dataset
            cache (bool): Whether to use caching
            
        Returns:
            Dict[str, Any]: Missing value analysis including counts, percentages, and patterns
        """
        try:
            cache_key = self._get_cache_key("missing_values", {"shape": data.shape})
            
            if cache:
                cached_result = redis_store.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit for missing values detection: {cache_key}")
                    return json.loads(cached_result)
            
            result = self.engine.detect_missing_values(data)
            
            if cache:
                redis_store.setex(
                    cache_key,
                    3600,  # Cache for 1 hour
                    json.dumps(result, default=str)
                )
                logger.debug(f"Missing values detection cached: {cache_key}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error detecting missing values: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def generate_pairplot(self, data: pd.DataFrame, columns: Optional[List[str]] = None, 
                         color_col: Optional[str] = None, cache: bool = True) -> str:
        """
        Generate pairplot (scatter plot matrix) for multiple variables.
        
        Args:
            data (pd.DataFrame): Input dataset
            columns (Optional[List[str]]): List of column names to include. If None, use all numeric columns.
            color_col (Optional[str]): Column name for color encoding
            cache (bool): Whether to use caching
            
        Returns:
            str: Plotly JSON representation of the pairplot
        """
        try:
            # Create params dict for cache key, using column names if provided
            if columns is None:
                cols_for_key = sorted([col for col in data.select_dtypes(include=[np.number]).columns])
            else:
                cols_for_key = sorted(columns)
                
            cache_key = self._get_cache_key("pairplot", {
                "columns": cols_for_key, "color": color_col, "shape": data.shape
            })
            
            if cache:
                cached_plot = redis_store.get(cache_key)
                if cached_plot:
                    logger.debug(f"Cache hit for pairplot: {cache_key}")
                    return cached_plot.decode('utf-8')
            
            fig = self.engine.generate_pairplot(data, columns, color_col)
            plot_json = fig.to_json()
            
            if cache:
                redis_store.setex(
                    cache_key,
                    1800,  # Cache for 30 minutes
                    plot_json.encode('utf-8')
                )
                logger.debug(f"Pairplot cached: {cache_key}")
                
            return plot_json
            
        except Exception as e:
            logger.error(f"Error generating pairplot: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def get_dataset_summary(self, data: pd.DataFrame, cache: bool = True) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the dataset.
        
        Args:
            data (pd.DataFrame): Input dataset
            cache (bool): Whether to use caching
            
        Returns:
            Dict[str, Any]: Dataset summary including basic info, memory usage, and variable types
        """
        try:
            cache_key = self._get_cache_key("dataset_summary", {"shape": data.shape})
            
            if cache:
                cached_summary = redis_store.get(cache_key)
                if cached_summary:
                    logger.debug(f"Cache hit for dataset summary: {cache_key}")
                    return json.loads(cached_summary)
            
            summary = self.engine.get_dataset_summary(data)
            
            if cache:
                redis_store.setex(
                    cache_key,
                    3600,  # Cache for 1 hour
                    json.dumps(summary, default=str)
                )
                logger.debug(f"Dataset summary cached: {cache_key}")
                
            return summary
            
        except Exception as e:
            logger.error(f"Error getting dataset summary: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def clear_cache(self):
        """
        Clear all cached data for this user.
        """
        try:
            # Use scan to find all keys with this user's prefix and delete them
            pattern = f"{self.cache_prefix}:*"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = redis_store.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    redis_store.delete(*keys)
                    deleted_count += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Cleared {deleted_count} cache entries for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing cache for user {self.user_id}: {str(e)}")
            raise
