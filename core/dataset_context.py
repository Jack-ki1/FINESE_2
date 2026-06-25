"""Dataset Context Module - Centralizes dataset information and metadata."""

import pandas as pd
import numpy as np
import hashlib
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

class DatasetContext:
    """Encapsulates all dataset information and provides consistent access to data and metadata."""
    
    def __init__(self, base_df: pd.DataFrame, filter_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the DatasetContext.
        
        Args:
            base_df: The original dataset
            filter_params: Parameters to apply to filter the data
        """
        self._base_df = base_df.copy() if base_df is not None else pd.DataFrame()
        self.filter_params = filter_params or {}
        self._filtered_df = None
        self._metadata = None
        
        # Compute dataset fingerprint
        self.dataset_fingerprint = self._compute_dataset_fingerprint(self._base_df)
        
        # Compute filter fingerprint
        self.filter_fingerprint = self._compute_filter_fingerprint(self.filter_params)
        
    def _compute_dataset_fingerprint(self, df: pd.DataFrame) -> str:
        """Compute a stable fingerprint for the dataset."""
        if df.empty:
            return "empty_dataset"
        
        # Sample the dataset to speed up fingerprinting
        sample_size = min(1000, len(df))
        sample_df = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df
        
        # Create a string representation of key characteristics
        fingerprint_str = (
            f"shape:{df.shape}_" +
            f"cols:{sorted(df.columns.tolist())}_" +
            f"dtypes:{str(sorted([(col, str(df[col].dtype)) for col in df.columns]))}_" +
            f"sample_hash:{hash(str(sample_df.values.flatten()[:1000]))}"
        )
        
        # Use SHA256 to create a stable hash
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]
    
    def _compute_filter_fingerprint(self, filter_params: Dict[str, Any]) -> str:
        """Compute a stable fingerprint for the filter parameters."""
        if not filter_params:
            return "no_filters"
        
        # Create a string representation of filter parameters
        sorted_items = sorted(filter_params.items(), key=lambda x: str(x[0]))
        filter_str = str(sorted_items)
        
        # Use SHA256 to create a stable hash
        return hashlib.sha256(filter_str.encode()).hexdigest()[:16]
    
    @property
    def base_df(self) -> pd.DataFrame:
        """Get the base (original) DataFrame."""
        return self._base_df
    
    @property
    def filtered_df(self) -> pd.DataFrame:
        """Get the filtered DataFrame, computing it if necessary."""
        if self._filtered_df is None:
            self._filtered_df = self._apply_filters()
        return self._filtered_df
    
    def _apply_filters(self) -> pd.DataFrame:
        """Apply the filter parameters to the base DataFrame."""
        if not self.filter_params:
            return self._base_df.copy()
        
        df = self._base_df.copy()
        
        # Apply filters based on the parameters
        for param_name, param_value in self.filter_params.items():
            if param_value is not None:
                if isinstance(param_value, dict) and 'range' in param_value:
                    # Range filter for numeric/date columns
                    col = param_value.get('column')
                    min_val = param_value.get('min')
                    max_val = param_value.get('max')
                    
                    if col and (min_val is not None or max_val is not None):
                        if min_val is not None:
                            df = df[df[col] >= min_val]
                        if max_val is not None:
                            df = df[df[col] <= max_val]
                            
                elif isinstance(param_value, list):
                    # Category filter
                    col = param_name.replace('_filter', '')
                    if col in df.columns:
                        df = df[df[col].isin(param_value)]
                        
                elif isinstance(param_value, str) and param_value in df.columns:
                    # Simple column selection
                    # This is handled differently depending on the use case
                    pass
        
        return df
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get computed metadata for the filtered DataFrame."""
        if self._metadata is None:
            self._metadata = self._compute_metadata()
        return self._metadata
    
    def _compute_metadata(self) -> Dict[str, Any]:
        """Compute metadata for the filtered DataFrame."""
        df = self.filtered_df
        
        if df.empty:
            return {
                'shape': (0, 0),
                'columns': [],
                'dtypes': {},
                'missing_info': {},
                'numeric_columns': [],
                'categorical_columns': [],
                'datetime_columns': [],
                'summary_stats': {}
            }
        
        # Compute basic metadata
        missing_info = df.isnull().sum()
        pct_missing = (missing_info / len(df) * 100).round(2)
        
        # Identify column types
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        categorical_cols = [col for col in df.columns if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col])]
        datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        
        # Prepare the metadata dictionary
        metadata = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': {col: str(df[col].dtype) for col in df.columns},
            'missing_info': {
                'count': missing_info.to_dict(),
                'percentage': pct_missing.to_dict()
            },
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols,
            'datetime_columns': datetime_cols,
            'summary_stats': df.describe().to_dict() if numeric_cols else {}
        }
        
        return metadata
    
    def get_column_stats(self, column_name: str) -> Dict[str, Any]:
        """Get statistics for a specific column."""
        if column_name not in self.filtered_df.columns:
            raise ValueError(f"Column {column_name} not found in filtered DataFrame")
        
        series = self.filtered_df[column_name]
        
        stats = {
            'missing_count': series.isnull().sum(),
            'missing_percentage': (series.isnull().sum() / len(series)) * 100,
            'unique_count': series.nunique(),
            'dtype': str(series.dtype)
        }
        
        if pd.api.types.is_numeric_dtype(series):
            stats.update({
                'mean': series.mean(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max(),
                'q25': series.quantile(0.25),
                'q50': series.quantile(0.50),
                'q75': series.quantile(0.75)
            })
        
        return stats
    
    def get_cache_key(self) -> str:
        """Get a combined cache key based on dataset and filter fingerprints."""
        return f"{self.dataset_fingerprint}_{self.filter_fingerprint}"
    
    def invalidate_cache(self):
        """Invalidate cached filtered data and metadata."""
        self._filtered_df = None
        self._metadata = None