from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

SESSION_DEFAULTS = {
    "base_df": None,
    "work_df": None,
    "filtered_data": None,
    "data_loaded": False,
    "theme": "light",
    "target_col": None,
    "problem_type": None,
    "selected_features": [],
    "learning_type": None,
    "pipeline": None,
    "leaderboard": None,
    "change_log": [],
    # ML-specific
    "encoding_method": "One-Hot Encoding",
    "scaling_method": "No Scaling",
    "missing_value_strategy": "Default (auto-detect)",
    "n_clusters": 3,
    "clustering_algo": "K-Means",
    "unsupervised_task": "Clustering",
    # Chatbot
    "chat_history": [],
    "llm_provider": "openai",
    "openai_api_key": "",
    "anthropic_api_key": "",
    "google_api_key": "",
    "llm_model": "gpt-4o-mini",
    # Global filters
    "selected_date_col": None,
    "date_range": None,
    "filtered_data_key": None,
    "cached_data_health": None,
    # Other UI states
    "selected_tab": "review",
    "last_operation": "",
    "operation_time": None,
    # Model deployment states
    "unsupervised_model": None,
    "cluster_labels": None,
    "X_processed": None,
    "dimensionality_reducer": None,
    "X_reduced": None,
    # Feature engineering
    "poly_degree": 2,
    "log_transform_features": [],
    "custom_features": False,
    "target_encoding_smoothing": 1.0,
    "outlier_handling": False,
    "apply_pca": False,
    "pca_components": 2,
    # Business goal and cost matrix
    "business_goal": "General purpose (balanced)",
    "model_cost": None,
}
"""
Flask session defaults. Streamlit code removed.
Use flask.session or core/dataset_store.py for state.
"""

DEFAULT_STATE = {
    'dataset_id': None,
    'dataset_name': None,
    'active_tab': 'review',
    'row_limit': 0,
    'dropped_columns': [],
    'cleaning_log': [],
    'chat_history': [],
    'ml_job_id': None,
    'last_chart_config': {},
}