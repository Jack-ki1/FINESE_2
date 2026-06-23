"""
FINESE2 - Service Layer
Business logic services for the application.
"""
from app.services.data_service import data_service
from app.services.data_processing_service import data_processing_service

# NOTE:
# app/services/eda_service.py defines an EDASer class (not an eda_service singleton).
# The previous import caused: ImportError: cannot import name 'eda_service'.
from app.services.eda_service import EDASer

from app.services.cleaning_service import cleaning_service
from app.services.visualization_service import visualization_service
from app.services.analysis_service import analysis_service
from app.services.ml_service import ml_service
from app.services.mlops_service import mlops_service
from app.services.report_service import report_service
from app.services.ai_service import ai_service

__all__ = [
    'data_service',
    'data_processing_service',
    'EDASer',
    'cleaning_service',
    'visualization_service',
    'analysis_service',
    'ml_service',
    'mlops_service',
    'report_service',
    'ai_service'
]

