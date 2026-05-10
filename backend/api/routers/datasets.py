from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import uuid
import hashlib
from datetime import datetime
import json

from ..schemas.datasets import DatasetSummary, FilteredDataset, DatasetUploadResponse
from ..services.dataset_service import DatasetService
from ..core.dependencies import get_current_user

router = APIRouter()

# Service instance
dataset_service = DatasetService()

class FilterParams(BaseModel):
    date_column: Optional[str] = None
    date_range: Optional[List[str]] = None  # [start_date, end_date]
    categorical_filters: Optional[Dict[str, List[str]]] = {}
    numeric_ranges: Optional[Dict[str, List[float]]] = {}  # {column: [min, max]}
    dropped_columns: Optional[List[str]] = []

class DatasetSessionCreate(BaseModel):
    name: str
    description: Optional[str] = None

@router.post("/", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: str = Depends(get_current_user)
):
    """
    Upload a new dataset (CSV, Excel, JSON)
    """
    try:
        # Read file content
        contents = await file.read()
        file_id = str(uuid.uuid4())
        
        # Determine file type and create DataFrame
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        elif file.filename.endswith('.json'):
            df = pd.read_json(io.StringIO(contents.decode('utf-8')))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Generate dataset fingerprint
        dataset_fingerprint = hashlib.sha256(contents).hexdigest()
        
        # Process and store the dataset
        dataset_id = await dataset_service.create_dataset(
            df, file_id, file.filename, dataset_fingerprint
        )
        
        # Calculate initial summary in background
        background_tasks.add_task(dataset_service.calculate_initial_summary, dataset_id)
        
        return DatasetUploadResponse(
            dataset_id=dataset_id,
            name=file.filename,
            fingerprint=dataset_fingerprint,
            summary=await dataset_service.get_dataset_summary(dataset_id)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}", response_model=DatasetSummary)
async def get_dataset_summary(
    dataset_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get summary information for a specific dataset
    """
    try:
        return await dataset_service.get_dataset_summary(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{dataset_id}/filters", response_model=FilteredDataset)
async def apply_filters(
    dataset_id: str,
    filters: FilterParams,
    current_user: str = Depends(get_current_user)
):
    """
    Apply filters to a dataset and return the filtered version
    """
    try:
        # Create a unique key for the filtered dataset based on filters
        filter_key = hashlib.sha256(json.dumps(filters.dict()).encode()).hexdigest()
        filtered_id = f"{dataset_id}_{filter_key}"
        
        # Check if this filtered dataset already exists in cache
        cached_result = await dataset_service.get_cached_filtered_dataset(filtered_id)
        if cached_result:
            return cached_result
            
        # Apply filters to the dataset
        filtered_df = await dataset_service.apply_filters(dataset_id, filters)
        
        # Create filtered dataset object
        filtered_dataset = FilteredDataset(
            filtered_id=filtered_id,
            original_dataset_id=dataset_id,
            filters_applied=filters.dict(),
            summary=await dataset_service.calculate_summary_for_dataframe(filtered_df)
        )
        
        # Cache the result
        await dataset_service.cache_filtered_dataset(filtered_id, filtered_dataset)
        
        return filtered_dataset
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/preview")
async def get_dataset_preview(
    dataset_id: str,
    rows: int = 10,
    current_user: str = Depends(get_current_user)
):
    """
    Get a preview of the dataset (first N rows)
    """
    try:
        preview_df = await dataset_service.get_dataset_preview(dataset_id, rows)
        return {"data": preview_df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Delete a dataset
    """
    try:
        await dataset_service.delete_dataset(dataset_id)
        return {"message": f"Dataset {dataset_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))