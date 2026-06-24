"""
FINESE2 - Consolidated Data Cleaning Module
Unified data cleaning operations and transformations
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer, KNNImputer
import warnings

logger = logging.getLogger(__name__)


class CleaningManager:
    """
    Unified data cleaning class combining all cleaning operations
    """

    def __init__(self):
        self.cleaning_operations = []
        self.scalers = {}
        self.encoders = {}
        self._last_cleaning_summary: Dict[str, Any] = {
            'operations_applied': [],
            'input_shape': None,
            'output_shape': None
        }
    
    def detect_issues(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect various data quality issues"""
        issues = {
            'missing_values': {},
            'duplicates': 0,
            'outliers': {},
            'inconsistent_types': [],
            'invalid_values': {},
            'skewed_columns': []
        }
        
        # Missing values
        missing = df.isnull().sum()
        issues['missing_values'] = {col: int(count) for col, count in missing.items() if count > 0}
        
        # Duplicates
        issues['duplicates'] = int(df.duplicated().sum())
        
        # Outliers detection for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            if len(outliers) > 0:
                issues['outliers'][col] = int(len(outliers))
        
        # Skewness detection
        for col in numeric_cols:
            skewness = df[col].skew()
            if abs(skewness) > 1:
                issues['skewed_columns'].append(col)
        
        # Invalid values (like infinite values)
        for col in numeric_cols:
            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                issues['invalid_values'][col] = int(inf_count)
        
        return issues
    
    def get_cleaning_recommendations(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Generate cleaning recommendations based on detected issues"""
        issues = self.detect_issues(df)
        recommendations = []
        
        if issues['missing_values']:
            recommendations.append({
                'type': 'missing_values',
                'action': 'Handle missing values',
                'details': f"Found {sum(issues['missing_values'].values())} missing values across {len(issues['missing_values'])} columns"
            })
        
        if issues['duplicates'] > 0:
            recommendations.append({
                'type': 'duplicates',
                'action': 'Remove duplicates',
                'details': f"Found {issues['duplicates']} duplicate rows"
            })
        
        if issues['outliers']:
            recommendations.append({
                'type': 'outliers',
                'action': 'Handle outliers',
                'details': f"Found outliers in {len(issues['outliers'])} columns"
            })
        
        if issues['skewed_columns']:
            recommendations.append({
                'type': 'skewed_data',
                'action': 'Apply transformation',
                'details': f"Found skewed columns: {', '.join(issues['skewed_columns'])}"
            })
        
        return recommendations
    
    def clean_dataset(self, df: pd.DataFrame, operations: List[Dict]) -> pd.DataFrame:
        """Apply cleaning operations to dataset"""
        cleaned_df = df.copy()

        # Reset summary for this run
        self._last_cleaning_summary = {
            'operations_applied': [],
            'input_shape': tuple(df.shape),
            'output_shape': None
        }

        for op in operations:
            op_type = op.get('operation')
            column = op.get('column')
            
            if op_type == 'remove_duplicates':
                cleaned_df = cleaned_df.drop_duplicates()
                
            elif op_type == 'fill_missing':
                strategy = op.get('strategy', 'mean')
                if column:
                    if strategy == 'mean':
                        cleaned_df[column].fillna(cleaned_df[column].mean(), inplace=True)
                    elif strategy == 'median':
                        cleaned_df[column].fillna(cleaned_df[column].median(), inplace=True)
                    elif strategy == 'mode':
                        cleaned_df[column].fillna(cleaned_df[column].mode()[0], inplace=True)
                    elif strategy == 'forward_fill':
                        cleaned_df[column].fillna(method='ffill', inplace=True)
                    elif strategy == 'backward_fill':
                        cleaned_df[column].fillna(method='bfill', inplace=True)
                    elif strategy == 'constant':
                        value = op.get('value', 0)
                        cleaned_df[column].fillna(value, inplace=True)
                        
            elif op_type == 'remove_outliers':
                method = op.get('method', 'iqr')
                if column and column in cleaned_df.columns:
                    if method == 'iqr':
                        Q1 = cleaned_df[column].quantile(0.25)
                        Q3 = cleaned_df[column].quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        cleaned_df = cleaned_df[
                            (cleaned_df[column] >= lower_bound) & 
                            (cleaned_df[column] <= upper_bound)
                        ]
                        
            elif op_type == 'normalize_column':
                method = op.get('method', 'standard')
                if column and column in cleaned_df.columns:
                    if method == 'standard':
                        scaler = StandardScaler()
                        cleaned_df[column] = scaler.fit_transform(cleaned_df[[column]])
                        self.scalers[column] = scaler
                    elif method == 'minmax':
                        scaler = MinMaxScaler()
                        cleaned_df[column] = scaler.fit_transform(cleaned_df[[column]])
                        self.scalers[column] = scaler
                        
            elif op_type == 'encode_categorical':
                method = op.get('method', 'label')
                if column and column in cleaned_df.columns:
                    if method == 'label':
                        le = LabelEncoder()
                        cleaned_df[column] = le.fit_transform(cleaned_df[column].astype(str))
                        self.encoders[column] = le
                    elif method == 'onehot':
                        dummies = pd.get_dummies(cleaned_df[column], prefix=column)
                        cleaned_df = pd.concat([cleaned_df, dummies], axis=1)
                        cleaned_df.drop(column, axis=1, inplace=True)
                        
            elif op_type == 'remove_column':
                if column and column in cleaned_df.columns:
                    cleaned_df.drop(column, axis=1, inplace=True)
                    
            elif op_type == 'transform_skewed':
                method = op.get('method', 'log')
                if column and column in cleaned_df.columns:
                    if method == 'log':
                        cleaned_df[column] = np.log1p(cleaned_df[column] - cleaned_df[column].min() + 1)
                    elif method == 'sqrt':
                        cleaned_df[column] = np.sqrt(cleaned_df[column] - cleaned_df[column].min() + 1)
                    elif method == 'boxcox':
                        from scipy import stats
                        cleaned_df[column], _ = stats.boxcox(cleaned_df[column] - cleaned_df[column].min() + 1)

            # Record applied operation (best effort)
            self._last_cleaning_summary['operations_applied'].append(op)

        self._last_cleaning_summary['output_shape'] = tuple(cleaned_df.shape)
        return cleaned_df
    
    def apply_cleaning_operations(self, df: pd.DataFrame, operations: List[Dict]) -> pd.DataFrame:
        """
        Compatibility wrapper expected by app/routes/api/data_ops.py

        Route passes `operations` as cleaning_operations.
        We map directly onto clean_dataset operations.
        """
        if operations is None:
            operations = []
        if not isinstance(operations, list):
            raise ValueError('operations must be a list')

        return self.clean_dataset(df, operations)

    def get_cleaning_summary(self) -> Dict[str, Any]:
        """Return the summary from the most recent cleaning run."""
        return self._last_cleaning_summary

    def impute_missing_values(self, df: pd.DataFrame, strategy: str = 'mean',
                            columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Impute missing values using various strategies"""
        df_imputed = df.copy()
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if strategy == 'mean':
            imputer = SimpleImputer(strategy='mean')
        elif strategy == 'median':
            imputer = SimpleImputer(strategy='median')
        elif strategy == 'most_frequent':
            imputer = SimpleImputer(strategy='most_frequent')
        elif strategy == 'knn':
            imputer = KNNImputer(n_neighbors=5)
        else:
            raise ValueError(f"Unknown imputation strategy: {strategy}")
        
        df_imputed[columns] = imputer.fit_transform(df_imputed[columns])
        
        return df_imputed
    
    def remove_outliers_iqr(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Remove outliers using IQR method"""
        df_filtered = df.copy()
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df_filtered = df_filtered[
                (df_filtered[col] >= lower_bound) & 
                (df_filtered[col] <= upper_bound)
            ]
        
        return df_filtered
    
    def normalize_data(self, df: pd.DataFrame, method: str = 'standard', 
                      columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Normalize data using various methods"""
        df_normalized = df.copy()
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        elif method == 'robust':
            from sklearn.preprocessing import RobustScaler
            scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        df_normalized[columns] = scaler.fit_transform(df_normalized[columns])
        # Store scaler for potential inverse transformation
        self.scalers[method] = scaler
        
        return df_normalized


# Global instance
cleaning_manager = CleaningManager()