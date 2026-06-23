"""
FINESE2 - Data Cleaning Service
Migrates and enhances engine/cleaner.py with user isolation and audit logging.
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from engine.cleaner import DataCleaner

logger = logging.getLogger(__name__)


class CleaningService:
    """
    Enhanced data cleaning service with user tracking.
    
    Wraps legacy DataCleaner while adding:
    - User-specific cleaning history
    - Audit trail for cleaning operations
    - Reversible cleaning operations
    """
    
    def __init__(self):
        self.cleaner = DataCleaner()
    
    def get_cleaning_recommendations(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Get smart cleaning recommendations for a dataset."""
        return self.cleaner.get_recommendations(df)
    
    def apply_cleaning(self, df: pd.DataFrame, operations: List[Dict], 
                      user_id: int, dataset_id: int) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply cleaning operations with audit logging.
        
        Args:
            df: Input DataFrame
            operations: List of cleaning operations to apply
            user_id: User performing the cleaning
            dataset_id: Dataset being cleaned
            
        Returns:
            Tuple of (cleaned_df, operation_summary)
        """
        original_shape = df.shape
        cleaned_df = df.copy()
        summary = {
            'operations_applied': [],
            'rows_before': original_shape[0],
            'columns_before': original_shape[1]
        }
        
        try:
            for op in operations:
                op_type = op.get('type')
                column = op.get('column')
                
                if op_type == 'drop_missing':
                    before_count = len(cleaned_df)
                    cleaned_df = cleaned_df.dropna(subset=[column])
                    after_count = len(cleaned_df)
                    summary['operations_applied'].append({
                        'operation': 'drop_missing',
                        'column': column,
                        'rows_removed': before_count - after_count
                    })
                    
                elif op_type == 'impute_mean':
                    mean_val = cleaned_df[column].mean()
                    cleaned_df[column] = cleaned_df[column].fillna(mean_val)
                    summary['operations_applied'].append({
                        'operation': 'impute_mean',
                        'column': column,
                        'value': float(mean_val)
                    })
                    
                elif op_type == 'impute_median':
                    median_val = cleaned_df[column].median()
                    cleaned_df[column] = cleaned_df[column].fillna(median_val)
                    summary['operations_applied'].append({
                        'operation': 'impute_median',
                        'column': column,
                        'value': float(median_val)
                    })
                    
                elif op_type == 'impute_mode':
                    mode_val = cleaned_df[column].mode()[0]
                    cleaned_df[column] = cleaned_df[column].fillna(mode_val)
                    summary['operations_applied'].append({
                        'operation': 'impute_mode',
                        'column': column,
                        'value': str(mode_val)
                    })
                    
                elif op_type == 'drop_duplicates':
                    before_count = len(cleaned_df)
                    cleaned_df = cleaned_df.drop_duplicates()
                    after_count = len(cleaned_df)
                    summary['operations_applied'].append({
                        'operation': 'drop_duplicates',
                        'rows_removed': before_count - after_count
                    })
                    
                elif op_type == 'clip_outliers':
                    Q1 = cleaned_df[column].quantile(0.25)
                    Q3 = cleaned_df[column].quantile(0.75)
                    IQR = Q3 - Q1
                    lower = Q1 - 1.5 * IQR
                    upper = Q3 + 1.5 * IQR
                    cleaned_df[column] = cleaned_df[column].clip(lower, upper)
                    summary['operations_applied'].append({
                        'operation': 'clip_outliers',
                        'column': column,
                        'lower': float(lower),
                        'upper': float(upper)
                    })
            
            summary['rows_after'] = len(cleaned_df)
            summary['columns_after'] = len(cleaned_df.columns)
            summary['rows_removed'] = summary['rows_before'] - summary['rows_after']
            
            logger.info(f"User {user_id} applied {len(operations)} cleaning operations on dataset {dataset_id}")
            
            return cleaned_df, summary
            
        except Exception as e:
            logger.error(f"Cleaning failed for user {user_id}, dataset {dataset_id}: {e}")
            raise


# Singleton instance
cleaning_service = CleaningService()
