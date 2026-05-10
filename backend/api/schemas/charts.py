from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChartPayload(BaseModel):
    chart_type: str
    title: str
    data: List[Dict[str, Any]]  # Chart-ready series data
    x_axis_label: str
    y_axis_label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}  # Additional chart info