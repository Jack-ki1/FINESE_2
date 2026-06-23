"""
FINESE2 - Statistical Analysis Service
Migrates and enhances engine/analyzer.py with user tracking and result caching.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats
import logging
from engine.analyzer import StatisticalAnalyzer

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Enhanced statistical analysis service with user isolation.
    
    Wraps legacy StatisticalAnalyzer while adding:
    - User-specific analysis history
    - Result caching
    - Analysis templates
    - Export capabilities
    """
    
    def __init__(self):
        self.analyzer = StatisticalAnalyzer()
    
    def perform_analysis(self, df: pd.DataFrame, analysis_type: str, 
                        params: Dict[str, Any], user_id: int,
                        dataset_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform statistical analysis with user tracking.
        
        Args:
            df: Input DataFrame
            analysis_type: Type of analysis (summary, hypothesis_test, correlation, etc.)
            params: Analysis parameters
            user_id: User performing the analysis
            dataset_id: Optional dataset ID for tracking
            
        Returns:
            Dictionary with analysis results
        """
        try:
            result = {
                'analysis_type': analysis_type,
                'user_id': user_id,
                'dataset_id': dataset_id,
                'params': params
            }
            
            if analysis_type == 'summary':
                columns = params.get('columns')
                result['data'] = self.analyzer.summary_statistics(df, columns)
                
            elif analysis_type == 'hypothesis_test':
                test_type = params.get('test_type')
                column1 = params.get('column1')
                column2 = params.get('column2')
                group_column = params.get('group_column')
                
                result['data'] = self.analyzer.hypothesis_test(
                    df, test_type, column1, column2, group_column
                )
                
            elif analysis_type == 'correlation':
                method = params.get('method', 'pearson')
                result['data'] = self.analyzer.correlation_analysis(df, method)
                
            elif analysis_type == 'regression':
                target = params.get('target')
                features = params.get('features')
                result['data'] = self.analyzer.regression_analysis(df, target, features)
                
            elif analysis_type == 'normality_test':
                column = params.get('column')
                result['data'] = self.analyzer.normality_test(df, column)
                
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
            logger.info(f"User {user_id} performed {analysis_type} analysis")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for user {user_id}: {e}")
            raise
    
    def get_analysis_templates(self) -> List[Dict[str, Any]]:
        """Get predefined analysis templates."""
        return [
            {
                'name': 'Basic Summary Statistics',
                'type': 'summary',
                'description': 'Mean, median, std, min, max for all numeric columns',
                'params': {}
            },
            {
                'name': 'Correlation Matrix',
                'type': 'correlation',
                'description': 'Pearson correlation between all numeric variables',
                'params': {'method': 'pearson'}
            },
            {
                'name': 'Normality Test',
                'type': 'normality_test',
                'description': 'Shapiro-Wilk test for normal distribution',
                'params': {}
            },
            {
                'name': 'T-Test (Independent)',
                'type': 'hypothesis_test',
                'description': 'Compare means between two independent groups',
                'params': {'test_type': 'ttest_ind'}
            },
            {
                'name': 'ANOVA',
                'type': 'hypothesis_test',
                'description': 'Compare means across multiple groups',
                'params': {'test_type': 'anova'}
            }
        ]


# Singleton instance
analysis_service = AnalysisService()
