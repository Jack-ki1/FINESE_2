from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd

from ..schemas.charts import ChartPayload
from ..services.chart_service import ChartService
from ..core.dependencies import get_current_user

router = APIRouter()

# Service instance
chart_service = ChartService()

class ChartRequest(BaseModel):
    dataset_id: str
    chart_type: str  # 'bar', 'line', 'scatter', 'histogram', 'heatmap', etc.
    x_axis: str
    y_axis: Optional[str] = None
    group_by: Optional[str] = None
    filters: Optional[Dict[str, Any]] = {}

@router.post("/", response_model=ChartPayload)
async def create_chart(
    request: ChartRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    Create a chart based on the specified parameters
    """
    try:
        # Check if we have a cached result
        chart_key = f"{request.dataset_id}_{request.chart_type}_{request.x_axis}_{request.y_axis}"
        cached_result = await chart_service.get_cached_chart_data(chart_key)
        if cached_result:
            return cached_result
            
        # Generate the chart data
        chart_payload = await chart_service.generate_chart(
            dataset_id=request.dataset_id,
            chart_type=request.chart_type,
            x_axis=request.x_axis,
            y_axis=request.y_axis,
            group_by=request.group_by,
            filters=request.filters
        )
        
        # Cache the result
        await chart_service.cache_chart_data(chart_key, chart_payload)
        
        return chart_payload
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/available-columns")
async def get_available_columns(
    dataset_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get available columns for charting
    """
    try:
        columns_info = await chart_service.get_column_info_for_charting(dataset_id)
        return {"columns": columns_info}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))