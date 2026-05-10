from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from ..schemas.jobs import JobStatus, JobResponse
from ..services.job_service import JobService
from ..core.dependencies import get_current_user

router = APIRouter()

job_service = JobService()

class JobRequest(BaseModel):
    job_type: str  # 'profile', 'train_model', 'export', etc.
    dataset_id: str
    parameters: Optional[Dict[str, Any]] = {}

@router.post("/", response_model=JobResponse)
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    Create a new background job
    """
    try:
        job_id = await job_service.create_job(
            job_type=request.job_type,
            dataset_id=request.dataset_id,
            parameters=request.parameters
        )
        
        # Add the actual job processing to background tasks
        if request.job_type == "profile":
            background_tasks.add_task(job_service.run_profiling_job, job_id)
        elif request.job_type == "train_model":
            background_tasks.add_task(job_service.run_model_training_job, job_id)
        elif request.job_type == "export":
            background_tasks.add_task(job_service.run_export_job, job_id)
        else:
            # For unknown job types, just mark as completed
            await job_service.complete_job(job_id, {"result": f"Completed {request.job_type} job"})
        
        return JobResponse(
            job_id=job_id,
            job_type=request.job_type,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            dataset_id=request.dataset_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get the status of a job
    """
    try:
        job_info = await job_service.get_job_status(job_id)
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job_info
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Cancel a running job
    """
    try:
        success = await job_service.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or already completed")
        
        return {"message": f"Job {job_id} cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))