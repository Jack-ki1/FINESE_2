from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from ..schemas.ml_models import ModelTrainingRequest, ModelTrainingResponse
from ..services.ml_service import MlService
from ..core.dependencies import get_current_user

router = APIRouter()

ml_service = MlService()

@router.post("/train", response_model=ModelTrainingResponse)
async def train_model(
    request: ModelTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    Train a machine learning model
    """
    try:
        model_id = await ml_service.initiate_training(
            dataset_id=request.dataset_id,
            target_column=request.target_column,
            model_type=request.model_type,
            features=request.features,
            parameters=request.parameters
        )
        
        # Run training in the background
        background_tasks.add_task(ml_service.perform_training, model_id)
        
        return ModelTrainingResponse(
            model_id=model_id,
            status="training_initiated",
            dataset_id=request.dataset_id,
            target_column=request.target_column,
            created_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{model_id}")
async def get_model_info(
    model_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get information about a trained model
    """
    try:
        model_info = await ml_service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model_info
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{model_id}/predict")
async def make_prediction(
    model_id: str,
    data: List[Dict[str, Any]],
    current_user: str = Depends(get_current_user)
):
    """
    Make predictions using a trained model
    """
    try:
        predictions = await ml_service.make_predictions(model_id, data)
        return {"predictions": predictions}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{model_id}/download")
async def download_model(
    model_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Download a trained model file
    """
    try:
        model_bytes = await ml_service.get_model_bytes(model_id)
        if not model_bytes:
            raise HTTPException(status_code=404, detail="Model file not found")
        
        from fastapi.responses import StreamingResponse
        import io
        return StreamingResponse(
            io.BytesIO(model_bytes),
            media_type='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename=model_{model_id}.pkl"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))