from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobResponse(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    progress: Optional[float] = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    dataset_id: str