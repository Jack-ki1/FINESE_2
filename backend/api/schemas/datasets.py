from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class ColumnInfo(BaseModel):
    name: str
    dtype: str
    missing_count: int
    missing_percentage: float
    unique_count: int

class DatasetSummary(BaseModel):
    dataset_id: str
    name: str
    fingerprint: Optional[str] = None
    shape: tuple[int, int]
    columns: List[ColumnInfo]
    created_at: datetime
    updated_at: Optional[datetime] = None
    size_mb: float

class FilteredDataset(BaseModel):
    filtered_id: str
    original_dataset_id: str
    filters_applied: Dict[str, Any]
    summary: DatasetSummary

class DatasetUploadResponse(BaseModel):
    dataset_id: str
    name: str
    fingerprint: str
    summary: DatasetSummary