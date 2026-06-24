"""
API Routes Package

Consolidated API route blueprints for the FINESE2 platform.

This module only re-exports existing blueprints. Route registration
is handled directly in `app/routes/__init__.py`.
"""

from .data_ops import data_ops_bp
from .ml_ops import ml_ops_bp
from .dashboard_ops import dashboard_ops_bp
from .eda_ops import eda_ops_bp  # Added EDA operations

__all__ = [
    'data_ops_bp',
    'ml_ops_bp',
    'dashboard_ops_bp',
    'eda_ops_bp'  # Added to exports
]
