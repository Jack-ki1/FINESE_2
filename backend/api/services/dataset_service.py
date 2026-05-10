import pandas as pd
import asyncio
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import io
import json

from ..schemas.datasets import DatasetSummary, ColumnInfo, FilteredDataset
from .cache_service import CacheService

class DatasetService:
    def __init__(self):
        self.datasets: Dict[str, pd.DataFrame] = {}
        self.metadata: Dict[str, Any] = {}
        self.cache_service = CacheService()

    async def create_dataset(
        self, 
        df: pd.DataFrame, 
        file_id: str, 
        filename: str, 
        fingerprint: str
    ) -> str:
        """Create a new dataset and store it"""
        dataset_id = f"ds_{file_id}"
        
        # Optimize data types to save memory
        df_optimized = self._optimize_dtypes(df)
        
        # Store the dataset
        self.datasets[dataset_id] = df_optimized
        
        # Store metadata
        self.metadata[dataset_id] = {
            "id": dataset_id,
            "name": filename,
            "fingerprint": fingerprint,
            "created_at": datetime.now(),
            "size_mb": df_optimized.memory_usage(deep=True).sum() / (1024 * 1024),
            "shape": df_optimized.shape
        }
        
        return dataset_id

    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame dtypes to save memory"""
        df_optimized = df.copy()
        
        for col in df_optimized.select_dtypes('int64').columns:
            df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='integer')
        
        for col in df_optimized.select_dtypes('float64').columns:
            df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='float')
        
        for col in df_optimized.select_dtypes('object').columns:
            if df_optimized[col].nunique() / len(df_optimized) < 0.5:
                df_optimized[col] = df_optimized[col].astype('category')
        
        return df_optimized

    async def get_dataset_summary(self, dataset_id: str) -> DatasetSummary:
        """Get summary information for a dataset"""
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
            
        df = self.datasets[dataset_id]
        metadata = self.metadata[dataset_id]
        
        # Calculate column info
        columns_info = []
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_percentage = (missing_count / len(df)) * 100
            unique_count = df[col].nunique(dropna=False)
            
            columns_info.append(ColumnInfo(
                name=col,
                dtype=str(df[col].dtype),
                missing_count=missing_count,
                missing_percentage=round(missing_percentage, 2),
                unique_count=unique_count
            ))
        
        return DatasetSummary(
            dataset_id=dataset_id,
            name=metadata["name"],
            fingerprint=metadata["fingerprint"],
            shape=metadata["shape"],
            columns=columns_info,
            created_at=metadata["created_at"],
            size_mb=round(metadata["size_mb"], 2)
        )

    async def calculate_summary_for_dataframe(self, df: pd.DataFrame) -> DatasetSummary:
        """Calculate summary for a given dataframe"""
        # This is a simplified version - in a real implementation, 
        # we would store this in a temporary dataset
        temp_id = f"temp_{hashlib.sha256(pd.util.hash_pandas_object(df).values).hexdigest()[:8]}"
        
        columns_info = []
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_percentage = (missing_count / len(df)) * 100
            unique_count = df[col].nunique(dropna=False)
            
            columns_info.append(ColumnInfo(
                name=col,
                dtype=str(df[col].dtype),
                missing_count=missing_count,
                missing_percentage=round(missing_percentage, 2),
                unique_count=unique_count
            ))
        
        return DatasetSummary(
            dataset_id=temp_id,
            name="Temporary Dataset",
            fingerprint=None,
            shape=df.shape,
            columns=columns_info,
            created_at=datetime.now(),
            size_mb=round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        )

    async def apply_filters(self, dataset_id: str, filters) -> pd.DataFrame:
        """Apply filters to a dataset and return filtered dataframe"""
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
            
        df = self.datasets[dataset_id].copy()
        
        # Apply date range filter
        if filters.date_column and filters.date_range:
            try:
                df[filters.date_column] = pd.to_datetime(df[filters.date_column], errors="coerce")
                start_date, end_date = filters.date_range
                df = df[(df[filters.date_column] >= start_date) & (df[filters.date_column] <= end_date)]
            except Exception as e:
                print(f"Date filter error: {e}")
                
        # Apply categorical filters
        for col, values in filters.categorical_filters.items():
            if col in df.columns and values:
                df = df[df[col].astype(str).isin(values)]
        
        # Apply numeric range filters
        for col, range_values in filters.numeric_ranges.items():
            if col in df.columns and len(range_values) == 2:
                min_val, max_val = range_values
                df = df[(df[col] >= min_val) & (df[col] <= max_val)]
        
        # Drop specified columns
        if filters.dropped_columns:
            df = df.drop(columns=[col for col in filters.dropped_columns if col in df.columns])
        
        return df

    async def get_dataset_preview(self, dataset_id: str, rows: int = 10) -> pd.DataFrame:
        """Get a preview of the dataset (first N rows)"""
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
            
        df = self.datasets[dataset_id]
        return df.head(rows)

    async def get_cached_filtered_dataset(self, filtered_id: str) -> Optional[FilteredDataset]:
        """Get cached filtered dataset if it exists"""
        return await self.cache_service.get_filtered_dataset(filtered_id)

    async def cache_filtered_dataset(self, filtered_id: str, filtered_dataset: FilteredDataset):
        """Cache a filtered dataset"""
        await self.cache_service.cache_filtered_dataset(filtered_id, filtered_dataset)

    async def delete_dataset(self, dataset_id: str):
        """Delete a dataset"""
        if dataset_id in self.datasets:
            del self.datasets[dataset_id]
            if dataset_id in self.metadata:
                del self.metadata[dataset_id]
        else:
            raise ValueError(f"Dataset {dataset_id} not found")

    async def calculate_initial_summary(self, dataset_id: str):
        """Calculate initial summary in background"""
        # This would typically trigger more intensive analysis
        # like calculating correlations, detecting data types, etc.
        pass