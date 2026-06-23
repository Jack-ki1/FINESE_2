"""
FINESE2 - Data Processing Service
Migrates and enhances engine/data_manager.py with user isolation and database integration.
"""
import io
import json
import os
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from app.models.user import Dataset
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


class DataProcessingService:
    """
    Enhanced data processing service with user isolation and persistent storage.
    
    Wraps legacy DataManager functionality while adding:
    - User-specific dataset tracking
    - Database integration
    - File security
    - Metadata management
    """
    
    SUPPORTED_FORMATS = {
        "csv": {"ext": [".csv"], "mime": "text/csv"},
        "excel": {"ext": [".xlsx", ".xls"], "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        "json": {"ext": [".json"], "mime": "application/json"},
        "parquet": {"ext": [".parquet"], "mime": "application/octet-stream"},
    }

    @staticmethod
    def detect_format(filename: str) -> str:
        """Detect file format from extension."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        for fmt, info in DataProcessingService.SUPPORTED_FORMATS.items():
            if f".{ext}" in info["ext"]:
                return fmt
        return "unknown"

    @staticmethod
    def sample_dataframe(df: pd.DataFrame, max_rows: int = 10000) -> pd.DataFrame:
        """Return a sample of the dataframe if it exceeds max_rows."""
        if len(df) <= max_rows:
            return df
        frac = max_rows / len(df)
        return df.sample(frac=frac, random_state=42)

    @staticmethod
    def load_csv(file_bytes: bytes, encoding: str = "utf-8", sep: str = ",", 
                 decimal: str = ".", thousands: Optional[str] = None, 
                 sample_if_large: bool = True, max_rows: int = 10000) -> pd.DataFrame:
        """Load CSV file."""
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding, sep=sep, decimal=decimal,
                thousands=thousands, low_memory=False
            )
            if sample_if_large:
                df = DataProcessingService.sample_dataframe(df, max_rows)
            return df
        except UnicodeDecodeError:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding="latin1", sep=sep, decimal=decimal,
                thousands=thousands, low_memory=False
            )
            if sample_if_large:
                df = DataProcessingService.sample_dataframe(df, max_rows)
            return df

    @staticmethod
    def load_excel(file_bytes: bytes, sheet_name: Optional[str] = None, 
                   header: int = 0, sample_if_large: bool = True, 
                   max_rows: int = 10000):
        """Load Excel file."""
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        available_sheets = xl.sheet_names

        if sheet_name is None or sheet_name not in available_sheets:
            sheet_name = available_sheets[0]

        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=header)
        
        if sample_if_large:
            df = DataProcessingService.sample_dataframe(df, max_rows)
            
        return df, available_sheets

    @staticmethod
    def load_json(file_bytes: bytes, orient: Optional[str] = None, 
                  lines: bool = False, sample_if_large: bool = True, 
                  max_rows: int = 10000) -> pd.DataFrame:
        """Load JSON file."""
        content = file_bytes.decode('utf-8')

        if lines:
            df = pd.read_json(io.StringIO(content), lines=True)
        else:
            data = json.loads(content)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.json_normalize(data)
            else:
                df = pd.DataFrame([data])
        
        if sample_if_large:
            df = DataProcessingService.sample_dataframe(df, max_rows)
            
        return df

    @staticmethod
    def load_parquet(file_bytes: bytes, sample_if_large: bool = True, 
                     max_rows: int = 10000) -> pd.DataFrame:
        """Load Parquet file."""
        df = pd.read_parquet(io.BytesIO(file_bytes))
        if sample_if_large:
            df = DataProcessingService.sample_dataframe(df, max_rows)
        return df

    @staticmethod
    def export_to_csv(df: pd.DataFrame) -> bytes:
        """Export DataFrame to CSV bytes."""
        output = io.BytesIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    @staticmethod
    def export_to_excel(df: pd.DataFrame) -> bytes:
        """Export DataFrame to Excel bytes."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        return output.getvalue()

    @staticmethod
    def export_to_json(df: pd.DataFrame, orient: str = 'records') -> bytes:
        """Export DataFrame to JSON bytes."""
        json_str = df.to_json(orient=orient, indent=2)
        return json_str.encode('utf-8')

    @staticmethod
    def get_dataset_preview(dataset_id: int, user_id: int, 
                           rows: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get preview of a dataset (first N rows).
        
        Args:
            dataset_id: Dataset ID
            user_id: User ID for ownership verification
            rows: Number of rows to preview
            
        Returns:
            Dictionary with preview data or None
        """
        from app.services.data_service import data_service
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset or dataset.owner_id != user_id:
            return None
        
        df = data_service.load_dataframe(dataset_id, user_id)
        if df is None:
            return None
        
        # Sample if needed
        preview_df = df.head(rows)
        
        return {
            'columns': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'shape': list(df.shape),
            'preview': preview_df.to_dict(orient='records'),
            'missing': {col: int(df[col].isnull().sum()) for col in df.columns}
        }


# Singleton instance
data_processing_service = DataProcessingService()
