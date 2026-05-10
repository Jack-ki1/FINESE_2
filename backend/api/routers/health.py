from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import pandas as pd

from ..schemas.health import HealthScorecard
from ..services.health_service import HealthService
from ..core.dependencies import get_current_user

router = APIRouter()

# Service instance
health_service = HealthService()

@router.get("/{dataset_id}", response_model=HealthScorecard)
async def get_data_health_score(
    dataset_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Calculate and return the health scorecard for a dataset
    """
    try:
        # Check if we have a cached result
        cached_result = await health_service.get_cached_health_score(dataset_id)
        if cached_result:
            return cached_result
            
        # Calculate the health score
        health_scorecard = await health_service.calculate_health_score(dataset_id)
        
        # Cache the result
        await health_service.cache_health_score(dataset_id, health_scorecard)
        
        return health_scorecard
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{dataset_id}/diagnostics")
async def get_data_diagnostics(
    dataset_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get detailed diagnostics for a dataset
    """
    try:
        diagnostics = await health_service.generate_diagnostics(dataset_id)
        return diagnostics
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{dataset_id}/auto-insights")
async def generate_auto_insights(
    dataset_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Generate automated insights about the dataset
    """
    try:
        insights = await health_service.generate_auto_insights(dataset_id)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))