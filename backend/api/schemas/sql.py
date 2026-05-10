from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class SqlQueryRequest(BaseModel):
    dataset_id: str
    query: str

class SqlQueryResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time: float
    error_message: Optional[str] = None