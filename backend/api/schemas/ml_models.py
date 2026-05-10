from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ModelTrainingRequest(BaseModel):
    dataset_id: str
    target_column: str
    model_type: str = "auto"  # "auto", "regression", "classification", specific algorithm name
    features: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = {}

class ModelTrainingResponse(BaseModel):
    model_id: str
    status: str
    dataset_id: str
    target_column: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None