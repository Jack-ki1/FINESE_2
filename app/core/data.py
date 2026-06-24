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
        # Cache for loaded datasets (runtime)
        # dataset_id -> { df, user_id, upload_time, metadata, version, lineage }
        self.datasets: Dict[str, Dict[str, Any]] = {}

        base_dir = Path(os.path.dirname(os.path.dirname(__file__)))  # app/
        self.upload_folder = str(base_dir / 'dashboard' / 'uploads')
        self.storage_folder = str(base_dir / 'instance' / 'datasets')

        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.storage_folder, exist_ok=True)
    
    def upload_dataset(self, file_path: str, user_id: int = 0) -> Dict[str, Any]:
        """Upload and store a dataset (legacy API)."""
        try:
            dataset_id = hashlib.md5(f"{file_path}_{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]

            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
            elif file_ext == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            self._set_dataset(
                dataset_id=dataset_id,
                df=df,
                user_id=user_id,
                metadata=self._generate_metadata(df),
                lineage={'source': {'type': 'upload', 'file_path': file_path}, 'transformations': []},
                version=1
            )

            return {
                'dataset_id': dataset_id,
                'rows': int(df.shape[0]),
                'columns': int(df.shape[1]),
                'columns_list': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2) if os.path.exists(file_path) else None
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
    
    def _dataset_path(self, dataset_id: str, fmt: str = 'parquet') -> str:
        # Persist snapshots as parquet for speed/consistency
        suffix = 'parquet' if fmt == 'parquet' else 'csv'
        ext = '.parquet' if fmt == 'parquet' else '.csv'
        return str(Path(self.storage_folder) / f"{dataset_id}.{suffix}{ext}")

    def _set_dataset(
        self,
        dataset_id: str,
        df: pd.DataFrame,
        user_id: int,
        metadata: Dict[str, Any],
        lineage: Dict[str, Any],
        version: int
    ) -> None:
        # cache
        self.datasets[dataset_id] = {
            'df': df,
            'user_id': user_id,
            'upload_time': datetime.now(),
            'metadata': metadata,
            'lineage': lineage,
            'version': version
        }
        # persist snapshot (parquet best-effort)
        snap_path = str(Path(self.storage_folder) / f"{dataset_id}.parquet")
        try:
            df.to_parquet(snap_path, index=False)
        except Exception:
            # fallback to csv
            df.to_csv(str(Path(self.storage_folder) / f"{dataset_id}.csv"), index=False)

    # --- Route-expected API (B) ---

    def load_dataset_from_file(self, filepath: str, filename: str, user_id: int = 0) -> str:
        """Route wrapper for /upload."""
        result = self.upload_dataset(filepath, user_id=user_id)
        # dataset_id must be returned to caller
        return result['dataset_id']

    def load_dataset_from_source(self, source_type: str, source_config: Dict[str, Any], user_id: int = 0) -> str:
        """
        Minimal loader for route /load.
        source_config supports:
          - {"path": "..."} for local files
          - {"format": "csv|parquet|json|excel", "path": "..."} optional
        """
        if source_type not in ['file', 'local']:
            raise ValueError('Unsupported source_type (expected file/local)')

        path = source_config.get('path')
        if not path:
            raise ValueError('source_config.path is required')

        file_path = str(path)
        return self.load_dataset_from_file(file_path, os.path.basename(file_path), user_id=user_id)

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List datasets visible to the runtime."""
        out = []
        for dataset_id, rec in self.datasets.items():
            out.append({
                'dataset_id': dataset_id,
                'rows': int(rec['df'].shape[0]),
                'columns': int(rec['df'].shape[1]),
                'version': rec.get('version', 1),
                'upload_time': rec.get('upload_time').isoformat() if hasattr(rec.get('upload_time'), 'isoformat') else None
            })
        return out

    def preview_dataset(self, dataset_id: str, n: int = 50) -> Optional[Dict[str, Any]]:
        df = self.get_dataset(dataset_id)
        if df is None:
            return None
        head = df.head(n)
        return {
            'columns': head.columns.tolist(),
            'rows': len(head),
            'data': head.where(pd.notnull(head), None).values.tolist()
        }

    def update_dataset(self, dataset_id: str, df: pd.DataFrame, lineage_event: Optional[Dict[str, Any]] = None) -> None:
        if dataset_id not in self.datasets:
            raise ValueError('Dataset not found')

        current = self.datasets[dataset_id]
        new_version = int(current.get('version', 1)) + 1

        lineage = current.get('lineage', {'source': {}, 'transformations': []})
        transformations = lineage.get('transformations', [])
        if lineage_event:
            transformations.append(lineage_event)
        lineage['transformations'] = transformations

        self._set_dataset(
            dataset_id=dataset_id,
            df=df,
            user_id=int(current.get('user_id', 0)),
            metadata=self._generate_metadata(df),
            lineage=lineage,
            version=new_version
        )

    def apply_transformations(self, df: pd.DataFrame, transformations: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Minimal transform engine for route /transform.
        Supports list of operations with operation field:
          - remove_columns: {operation, columns:[...]}
          - rename_columns: {operation, mapping:{old:new}}
          - filter_rows: {operation, query:"col > 0"}  (pandas.query)
          - cast: {operation, dtypes:{col: "int"/"float"/"str"}}
        """
        out = df.copy()
        for t in transformations or []:
            op = t.get('operation')
            if not op:
                continue

            if op == 'remove_columns':
                cols = t.get('columns', [])
                out = out.drop(columns=[c for c in cols if c in out.columns], errors='ignore')

            elif op == 'rename_columns':
                mapping = t.get('mapping', {})
                out = out.rename(columns=mapping)

            elif op == 'filter_rows':
                query = t.get('query')
                if query:
                    out = out.query(query)

            elif op == 'cast':
                dtypes = t.get('dtypes', {})
                for col, dtype in dtypes.items():
                    if col in out.columns:
                        out[col] = out[col].astype(dtype, errors='ignore')

            else:
                raise ValueError(f"Unknown transformation operation: {op}")

        return out

    def get_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """Retrieve a cached dataset."""
        if dataset_id in self.datasets:
            return self.datasets[dataset_id]['df']
        # attempt reload from persisted snapshot
        snap_parquet = str(Path(self.storage_folder) / f"{dataset_id}.parquet")
        snap_csv = str(Path(self.storage_folder) / f"{dataset_id}.csv")
        if os.path.exists(snap_parquet):
            try:
                df = pd.read_parquet(snap_parquet)
                self._set_dataset(
                    dataset_id=dataset_id,
                    df=df,
                    user_id=0,
                    metadata=self._generate_metadata(df),
                    lineage={'source': {'type': 'snapshot', 'path': snap_parquet}, 'transformations': []},
                    version=1
                )
                return df
            except Exception:
                pass
        if os.path.exists(snap_csv):
            try:
                df = pd.read_csv(snap_csv)
                self._set_dataset(
                    dataset_id=dataset_id,
                    df=df,
                    user_id=0,
                    metadata=self._generate_metadata(df),
                    lineage={'source': {'type': 'snapshot', 'path': snap_csv}, 'transformations': []},
                    version=1
                )
                return df
            except Exception:
                pass
        return None

    def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a dataset."""
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