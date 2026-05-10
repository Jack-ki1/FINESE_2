from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import pandas as pd

from ..schemas.sql import SqlQueryRequest, SqlQueryResponse
from ..services.sql_service import SqlService
from ..core.dependencies import get_current_user

router = APIRouter()

sql_service = SqlService()

@router.post("/", response_model=SqlQueryResponse)
async def execute_sql_query(
    request: SqlQueryRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Execute a SQL query on the specified dataset
    """
    try:
        result_df = await sql_service.execute_query(
            dataset_id=request.dataset_id,
            query=request.query
        )
        
        # Convert DataFrame to records for JSON serialization
        result_data = result_df.to_dict(orient='records')
        
        return SqlQueryResponse(
            success=True,
            data=result_data,
            row_count=len(result_data),
            columns=list(result_df.columns),
            execution_time=0.0  # In a real implementation, measure actual execution time
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get the schema of a dataset (columns and types)
    """
    try:
        schema = await sql_service.get_dataset_schema(dataset_id)
        return schema
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))