from pydantic import BaseModel
from typing import Dict, List, Optional
from enum import Enum

class HealthCategory(Enum):
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"

class HealthScorecard(BaseModel):
    final_score: float  # Overall health score (0-100)
    details: Dict[HealthCategory, float]  # Scores for each category (0-100)
    diagnostics: Optional[Dict[str, Any]] = None  # Detailed diagnostic information
    recommendations: Optional[List[str]] = None  # Recommended actions
    generated_at: str  # Timestamp of when the scorecard was generated