"""
Services package for FINESE - Smart Data Explorer Pro
"""

# Import core services for easy access
from .health_service import calculate_data_health_score, generate_health_insights
from .chart_service import create_completeness_chart, create_missing_heatmap, create_outlier_analysis, create_correlation_heatmap, create_distribution_plots, MAX_ROWS_FOR_PLOT
from .cleaning_service import get_cleaning_suggestions, apply_cleaning_suggestions, suggest_optimal_type
from .profiling_service import generate_basic_profile_report, get_column_profiles, check_data_quality_issues
from .sql_service import execute_sql_query, get_table_schema, validate_sql_syntax
from .ml_service import prepare_ml_data, create_preprocessing_pipeline, train_model, evaluate_model, predict_with_model, save_model, load_model
from .llm_service import generate_data_summary, ask_question_about_data

__all__ = [
    # Health service
    'calculate_data_health_score', 
    'generate_health_insights',
    
    # Chart service
    'create_completeness_chart', 
    'create_missing_heatmap', 
    'create_outlier_analysis', 
    'create_correlation_heatmap', 
    'create_distribution_plots',
    'MAX_ROWS_FOR_PLOT',
    
    # Cleaning service
    'get_cleaning_suggestions', 
    'apply_cleaning_suggestions', 
    'suggest_optimal_type',
    
    # Profiling service
    'generate_basic_profile_report', 
    'get_column_profiles', 
    'check_data_quality_issues',
    
    # SQL service
    'execute_sql_query', 
    'get_table_schema', 
    'validate_sql_syntax',
    
    # ML service
    'prepare_ml_data', 
    'create_preprocessing_pipeline', 
    'train_model', 
    'evaluate_model', 
    'predict_with_model', 
    'save_model', 
    'load_model',
    
    # LLM service
    'generate_data_summary', 
    'ask_question_about_data'
]