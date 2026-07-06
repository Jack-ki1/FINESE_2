import os
import uuid
import json
import pandas as pd
from typing import Optional, Tuple
from datetime import datetime
from pathlib import Path

class DatasetStore:
    """Dataset storage using Parquet format instead of pickle for better performance and compatibility."""
    
    def __init__(self, base_path='static/uploads'):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(os.path.join(base_path, 'versions'), exist_ok=True)

    def _path(self, dataset_id):
        return os.path.join(self.base_path, f"{dataset_id}.parquet")

    def _meta_path(self, dataset_id):
        return os.path.join(self.base_path, f"{dataset_id}.meta.json")

    def save(self, df, name, dataset_id=None):
        """Save dataset using Parquet format."""
        if dataset_id is None:
            dataset_id = str(uuid.uuid4())
        
        # Save dataframe as Parquet
        path = self._path(dataset_id)
        df.to_parquet(path, index=False)
        
        # Save metadata
        meta_path = self._meta_path(dataset_id)
        with open(meta_path, 'w') as f:
            json.dump({
                'name': name,
                'shape': list(df.shape),
                'columns': list(df.columns),
                'created_at': datetime.now().isoformat()
            }, f)
        
        return dataset_id

    def load(self, dataset_id):
        """Load dataset from Parquet format."""
        path = self._path(dataset_id)
        if not os.path.exists(path):
            return None, None
        
        df = pd.read_parquet(path)
        
        meta_path = self._meta_path(dataset_id)
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            name = meta.get('name', 'Unknown')
        else:
            name = 'Unknown'
        
        return df, name

    def delete(self, dataset_id):
        """Delete dataset and its metadata."""
        path = self._path(dataset_id)
        meta_path = self._meta_path(dataset_id)
        
        if os.path.exists(path):
            os.remove(path)
        if os.path.exists(meta_path):
            os.remove(meta_path)

    def exists(self, dataset_id):
        """Check if dataset exists."""
        return os.path.exists(self._path(dataset_id))

    def save_version(self, df, name, dataset_id, version_note=''):
        """Save a versioned snapshot for undo support."""
        versions_path = os.path.join(self.base_path, 'versions')
        os.makedirs(versions_path, exist_ok=True)
        
        version_id = str(uuid.uuid4())
        version_path = os.path.join(versions_path, f"{version_id}.parquet")
        
        # Save the df snapshot
        df.to_parquet(version_path, index=False)
        
        # Create version metadata
        snapshot = {
            'version_id': version_id,
            'parent_dataset_id': dataset_id,
            'note': version_note,
            'timestamp': datetime.now().isoformat(),
            'shape': list(df.shape)
        }
        
        # Append to version log
        log_path = os.path.join(self.base_path, f"{dataset_id}.versions.json")
        history = []
        if os.path.exists(log_path):
            with open(log_path) as f:
                try:
                    history = json.load(f)
                except:
                    history = []
        
        history.append(snapshot)
        with open(log_path, 'w') as f:
            json.dump(history, f)
        
        return version_id

    def restore_version(self, version_id, dataset_id):
        """Restore a specific version."""
        versions_path = os.path.join(self.base_path, 'versions')
        version_path = os.path.join(versions_path, f"{version_id}.parquet")
        
        if not os.path.exists(version_path):
            return None, None
        
        df = pd.read_parquet(version_path)
        
        # Get original dataset name
        meta_path = self._meta_path(dataset_id)
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            name = meta.get('name', 'Unknown')
        else:
            name = 'Unknown'
        
        return df, name

    def get_version_history(self, dataset_id):
        """Get version history for a dataset."""
        log_path = os.path.join(self.base_path, f"{dataset_id}.versions.json")
        if not os.path.exists(log_path):
            return []
        
        with open(log_path) as f:
            try:
                return json.load(f)
            except:
                return []


# Global current dataset tracking (Flask session alternative)
_current_dataset_id: Optional[str] = None
_current_dataset_info: Optional[dict] = None

# Fix: store in Flask g or the session, not module globals
from flask import g, session

def set_current_dataset(dataset_id: str, name: str = None, shape: tuple = None) -> None:
    """Store current dataset info in Flask request context."""
    g.current_dataset = {
        'id': dataset_id,
        'name': name,
        'shape': list(shape) if shape else None,
    }

def get_current_dataset() -> Optional[dict]:
    """Get current dataset from Flask g context."""
    return getattr(g, 'current_dataset', None)

def clear_current_dataset() -> None:
    """Clear current dataset from Flask g context."""
    g.current_dataset = None
