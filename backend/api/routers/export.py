from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi.responses import StreamingResponse
import io

from ..services.export_service import ExportService
from ..core.dependencies import get_current_user

router = APIRouter()

export_service = ExportService()

class ExportRequest(BaseModel):
    dataset_id: str
    format: str = 'csv'  # csv, excel, json, parquet
    columns: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None

class ExportBundleRequest(BaseModel):
    dataset_id: str
    formats: List[str] = ['csv']
    include_report: bool = True

@router.post("/dataset")
async def export_dataset(
    request: ExportRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Export a dataset in the specified format
    """
    try:
        exported_data = await export_service.export_dataset(
            dataset_id=request.dataset_id,
            format=request.format,
            columns=request.columns,
            filters=request.filters
        )
        
        # Determine content type based on format
        content_types = {
            'csv': 'text/csv',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'json': 'application/json',
            'parquet': 'application/octet-stream'
        }
        
        content_type = content_types.get(request.format, 'application/octet-stream')
        
        return StreamingResponse(
            io.BytesIO(exported_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={request.dataset_id}.{request.format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/report")
async def export_report(
    dataset_id: str,
    report_type: str = 'summary',
    include_visualizations: bool = True,
    current_user: str = Depends(get_current_user)
):
    """
    Export a report about the dataset
    """
    try:
        report_data = await export_service.export_report(
            dataset_id=dataset_id,
            report_type=report_type,
            include_visualizations=include_visualizations
        )
        
        return StreamingResponse(
            io.BytesIO(report_data),
            media_type='application/json',
            headers={
                "Content-Disposition": f"attachment; filename={dataset_id}_report.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bundle")
async def export_bundle(
    request: ExportBundleRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Export a bundle with multiple formats and optionally a report
    """
    try:
        bundle_data = await export_service.export_bundle(
            dataset_id=request.dataset_id,
            formats=request.formats,
            include_report=request.include_report
        )
        
        return StreamingResponse(
            io.BytesIO(bundle_data),
            media_type='application/zip',
            headers={
                "Content-Disposition": f"attachment; filename={request.dataset_id}_bundle.zip"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))