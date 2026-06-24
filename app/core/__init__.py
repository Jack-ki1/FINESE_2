"""
FINESE2 - Core Modules Package
Initialization file for core modules package.
"""
from .data import data_manager
from .eda import eda_engine
from .cleaning import cleaning_manager
from .visualize import visualizer
from .analysis import analysis_engine
from .ml_models import ml_model_manager
from .mlops import mlops_manager
from .reports import report_generator
from .dashboard import dashboard_manager

__all__ = [
    'data_manager',
    'eda_engine',
    'cleaning_manager',
    'visualizer',
    'analysis_engine',
    'ml_model_manager',
    'mlops_manager',
    'report_generator',
    'dashboard_manager'
]