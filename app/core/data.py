"""
FINESE2 - Consolidated Data Management Module
Unified data operations including loading, preprocessing, and management
"""
import pandas as pd
import numpy as np
import os
import json
import sqlite3
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime
import logging
from io import StringIO
import tempfile
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


class DataManager:
    """
    Unified data management class combining all data operations
    """
    
    def __init__(self):
        self.datasets = {}  # Cache for loaded datasets
        self.upload_folder = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'dashboard',
            'uploads'
        )
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def upload_dataset(self, file_path: str, user_id: int) -> Dict[str, Any]:
        """Upload and store a dataset"""
        try:
            # Generate unique ID for dataset
            dataset_id = hashlib.md5(f"{file_path}_{user_id}_{datetime.now()}".encode()).hexdigest()
            
            # Determine file type and load appropriately
            file_ext = Path(file_path).suffix.lower()
            if file_ext in ['.csv']:
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_ext in ['.json']:
                df = pd.read_json(file_path)
            elif file_ext in ['.parquet']:
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Store in cache
            self.datasets[dataset_id] = {
                'df': df,
                'user_id': user_id,
                'upload_time': datetime.now(),
                'file_path': file_path,
                'metadata': self._generate_metadata(df)
            }
            
            return {
                'dataset_id': dataset_id,
                'rows': len(df),
                'columns': len(df.columns),
                'columns_list': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error uploading dataset: {e}")
            raise
    
    def load_sample_dataset(self, dataset_name: str) -> pd.DataFrame:
        """Load predefined sample datasets"""
        samples = {
            'iris': pd.DataFrame({
                'sepal_length': np.random.uniform(4.0, 8.0, 150),
                'sepal_width': np.random.uniform(2.0, 5.0, 150),
                'petal_length': np.random.uniform(1.0, 7.0, 150),
                'petal_width': np.random.uniform(0.1, 2.5, 150),
                'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 150)
            }),
            'titanic': pd.DataFrame({
                'survived': np.random.choice([0, 1], 1000),
                'pclass': np.random.choice([1, 2, 3], 1000),
                'sex': np.random.choice(['male', 'female'], 1000),
                'age': np.random.uniform(1, 80, 1000),
                'fare': np.random.uniform(5, 500, 1000),
                'embarked': np.random.choice(['C', 'Q', 'S'], 1000)
            }),
            'wine': pd.DataFrame({
                'alcohol': np.random.uniform(11.0, 15.0, 178),
                'malic_acid': np.random.uniform(0.5, 6.0, 178),
                'ash': np.random.uniform(1.5, 3.5, 178),
                'alcalinity_of_ash': np.random.uniform(10.0, 30.0, 178),
                'magnesium': np.random.randint(70, 170, 178),
                'total_phenols': np.random.uniform(0.5, 4.0, 178),
                'flavanoids': np.random.uniform(0.5, 5.0, 178),
                'class': np.random.choice([1, 2, 3], 178)
            })
        }
        
        if dataset_name not in samples:
            raise ValueError(f"Unknown sample dataset: {dataset_name}")
        
        return samples[dataset_name]
    
    def get_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """Retrieve a cached dataset"""
        if dataset_id in self.datasets:
            return self.datasets[dataset_id]['df']
        return None
    
    def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a dataset"""
        if dataset_id in self.datasets:
            return self.datasets[dataset_id]['metadata']
        return None
    
    def _generate_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate metadata for a dataframe"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        metadata = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': {col: str(df[col].dtype) for col in df.columns},
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols,
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_rows': int(df.duplicated().sum()),
            'basic_stats': {}
        }
        
        if numeric_cols:
            metadata['basic_stats'] = df[numeric_cols].describe().to_dict()
        
        return metadata
    
    def export_dataset(self, dataset_id: str, export_format: str = 'csv') -> str:
        """Export dataset in specified format"""
        df = self.get_dataset(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f'.{export_format}',
            dir=self.upload_folder
        )
        
        if export_format == 'csv':
            df.to_csv(temp_file.name, index=False)
        elif export_format == 'excel':
            df.to_excel(temp_file.name, index=False)
        elif export_format == 'json':
            df.to_json(temp_file.name, orient='records', indent=2)
        elif export_format == 'parquet':
            df.to_parquet(temp_file.name, index=False)
        
        return temp_file.name
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset from cache"""
        if dataset_id in self.datasets:
            del self.datasets[dataset_id]
            return True
        return False


# Global instance
data_manager = DataManager()