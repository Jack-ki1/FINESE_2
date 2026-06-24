"""
FINESE2 - Consolidated Analysis Module
Comprehensive statistical analysis capabilities
"""
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import ttest_ind, f_oneway, chi2_contingency
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

class AnalysisEngine:
    """
    Consolidated analysis engine providing comprehensive statistical analysis capabilities.
    """
    
    def __init__(self):
        self.results = {}
    
    def descriptive_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive descriptive statistics."""
        numeric_df = df.select_dtypes(include=[np.number])
        
        stats_result = {
            'overall': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_columns': len(numeric_df.columns),
                'categorical_columns': len(df.select_dtypes(include=['object', 'category']).columns),
                'memory_usage_mb': float(df.memory_usage(deep=True).sum() / (1024 * 1024))
            },
            'numeric': {},
            'categorical': {}
        }
        
        # Numeric statistics
        if not numeric_df.empty:
            stats_result['numeric'] = numeric_df.describe().to_dict()
            
            # Additional statistics
            for col in numeric_df.columns:
                col_data = numeric_df[col].dropna()
                if len(col_data) > 1:  # Need at least 2 values for these calculations
                    stats_result['numeric'][col]['skewness'] = float(col_data.skew())
                    stats_result['numeric'][col]['kurtosis'] = float(col_data.kurtosis())
                    stats_result['numeric'][col]['variance'] = float(col_data.var())
                    stats_result['numeric'][col]['std_error_mean'] = float(stats.sem(col_data))
        
        # Categorical statistics
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            col_data = df[col].dropna()
            stats_result['categorical'][col] = {
                'unique_count': int(col_data.nunique()),
                'top_category': col_data.mode().iloc[0] if not col_data.empty else None,
                'top_category_count': int(col_data.value_counts().iloc[0]) if not col_data.empty else 0,
                'entropy': float(self._calculate_entropy(col_data))
            }
        
        self.results['descriptive'] = stats_result
        return stats_result
    
    def hypothesis_tests(self, df: pd.DataFrame, test_type: str, 
                        group_col: Optional[str] = None, 
                        value_col: Optional[str] = None) -> Dict[str, Any]:
        """Perform various hypothesis tests."""
        if test_type == 't_test':
            if group_col is None or value_col is None:
                raise ValueError("Both group_col and value_col required for t-test")
            
            groups = df.groupby(group_col)[value_col].apply(list)
            if len(groups) != 2:
                raise ValueError("T-test requires exactly 2 groups")
            
            group1, group2 = groups.iloc[0], groups.iloc[1]
            t_stat, p_val = ttest_ind(group1, group2)
            
            return {
                'test': 'Independent T-Test',
                'statistic': float(t_stat),
                'p_value': float(p_val),
                'significant': p_val < 0.05,
                'interpretation': 'Significant difference' if p_val < 0.05 else 'No significant difference'
            }
        
        elif test_type == 'anova':
            if group_col is None or value_col is None:
                raise ValueError("Both group_col and value_col required for ANOVA")
            
            groups = df.groupby(group_col)[value_col].apply(list)
            if len(groups) < 2:
                raise ValueError("ANOVA requires at least 2 groups")
            
            f_stat, p_val = f_oneway(*groups)
            
            return {
                'test': 'One-way ANOVA',
                'statistic': float(f_stat),
                'p_value': float(p_val),
                'significant': p_val < 0.05,
                'interpretation': 'At least one group mean is significantly different' if p_val < 0.05 else 'No significant differences between group means'
            }
        
        elif test_type == 'chi_square':
            if group_col is None or value_col is None:
                raise ValueError("Both group_col and value_col required for Chi-Square test")
            
            contingency_table = pd.crosstab(df[group_col], df[value_col])
            chi2, p_val, dof, expected = chi2_contingency(contingency_table)
            
            return {
                'test': 'Chi-Square Test of Independence',
                'statistic': float(chi2),
                'p_value': float(p_val),
                'degrees_of_freedom': int(dof),
                'significant': p_val < 0.05,
                'interpretation': 'Variables are dependent' if p_val < 0.05 else 'Variables are independent'
            }
        
        else:
            raise ValueError(f"Unknown test type: {test_type}")
    
    def correlation_analysis(self, df: pd.DataFrame, method: str = 'pearson') -> Dict[str, Any]:
        """Perform correlation analysis."""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return {"error": "No numeric columns found for correlation analysis"}
        
        corr_matrix = numeric_df.corr(method=method)
        
        # Identify significant correlations
        significant_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.5:  # Moderate correlation threshold
                    significant_pairs.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': float(corr_val),
                        'strength': 'strong' if abs(corr_val) > 0.7 else 'moderate'
                    })
        
        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'significant_correlations': significant_pairs,
            'correlation_method': method
        }
    
    def regression_analysis(self, df: pd.DataFrame, target_col: str, 
                           feature_cols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform basic regression analysis."""
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
            
            if feature_cols is None:
                feature_cols = [col for col in df.columns if col != target_col and pd.api.types.is_numeric_dtype(df[col])]
            
            X = df[feature_cols].select_dtypes(include=[np.number])
            y = df[target_col].select_dtypes(include=[np.number])
            
            if X.empty or y.empty:
                return {"error": "No suitable numeric data for regression analysis"}
            
            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(y.mean())
            
            model = LinearRegression()
            model.fit(X, y)
            
            y_pred = model.predict(X)
            
            r2 = r2_score(y, y_pred)
            mse = mean_squared_error(y, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y, y_pred)
            
            # Feature importance (coefficients)
            feature_importance = dict(zip(feature_cols, model.coef_))
            
            return {
                'model_type': 'Linear Regression',
                'r_squared': float(r2),
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'intercept': float(model.intercept_),
                'feature_importance': feature_importance,
                'predictions': y_pred.tolist()[:10],  # Return first 10 predictions
                'actual': y.tolist()[:10]  # Return first 10 actual values
            }
            
        except ImportError:
            return {"error": "scikit-learn not available for regression analysis"}
    
    def distribution_tests(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Test if a column follows a particular distribution."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        
        series = df[column].dropna()
        
        if len(series) < 8:
            return {"error": "Insufficient data for distribution testing (minimum 8 samples)"}
        
        # Test for normality using Shapiro-Wilk test
        try:
            shapiro_stat, shapiro_p = stats.shapir(series[:5000])  # Limit to 5000 samples for efficiency
            is_normal = shapiro_p > 0.05
        except ValueError:
            # If sample is too small for Shapiro-Wilk, skip this test
            shapiro_stat, shapiro_p, is_normal = None, None, False
        
        # Additional tests for different distributions
        distribution_tests = {}
        
        # Kolmogorov-Smirnov test for normality
        if len(series) > 3:  # KS test needs at least 3 samples
            ks_stat, ks_p = stats.kstest(series, 'norm')
            distribution_tests['kolmogorov_smirnov'] = {
                'statistic': float(ks_stat),
                'p_value': float(ks_p),
                'follows_normal': ks_p > 0.05
            }
        
        return {
            'column': column,
            'shapiro_wilk': {
                'statistic': shapiro_stat,
                'p_value': shapiro_p,
                'follows_normal': is_normal
            },
            'kolmogorov_smirnov': distribution_tests.get('kolmogorov_smirnov'),
            'sample_size': len(series),
            'recommended_distribution': 'normal' if is_normal else 'non-normal'
        }
    
    def time_series_analysis(self, df: pd.DataFrame, date_col: str, 
                            value_col: str) -> Dict[str, Any]:
        """Basic time series analysis."""
        if date_col not in df.columns or value_col not in df.columns:
            raise ValueError(f"Columns '{date_col}' or '{value_col}' not found")
        
        ts_df = df[[date_col, value_col]].copy()
        
        # Convert date column to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(ts_df[date_col]):
            ts_df[date_col] = pd.to_datetime(ts_df[date_col])
        
        ts_df.set_index(date_col, inplace=True)
        ts_df.sort_index(inplace=True)
        
        # Basic time series statistics
        analysis = {
            'start_date': ts_df.index.min().isoformat() if not ts_df.empty else None,
            'end_date': ts_df.index.max().isoformat() if not ts_df.empty else None,
            'frequency': None,
            'trend': None,
            'seasonality': None,
            'volatility': float(ts_df[value_col].std()) if not ts_df.empty else None,
            'mean': float(ts_df[value_col].mean()) if not ts_df.empty else None,
            'min': float(ts_df[value_col].min()) if not ts_df.empty else None,
            'max': float(ts_df[value_col].max()) if not ts_df.empty else None
        }
        
        # Try to infer frequency
        if len(ts_df) > 1:
            time_diffs = ts_df.index.to_series().diff().dropna()
            most_common_freq = time_diffs.mode().iloc[0] if not time_diffs.empty else None
            if most_common_freq:
                analysis['frequency'] = str(most_common_freq)
        
        # Simple trend analysis (using linear regression)
        if len(ts_df) > 2:
            try:
                x_vals = np.arange(len(ts_df))
                y_vals = ts_df[value_col].values
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
                
                analysis['trend'] = {
                    'slope': float(slope),
                    'r_squared': float(r_value**2),
                    'significant': p_value < 0.05,
                    'direction': 'increasing' if slope > 0 else 'decreasing'
                }
            except:
                analysis['trend'] = None
        
        return analysis
    
    def feature_importance_analysis(self, df: pd.DataFrame, target_col: str,
                                   method: str = 'correlation') -> Dict[str, Any]:
        """Analyze feature importance relative to target."""
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found")
        
        numeric_df = df.select_dtypes(include=[np.number]).copy()
        
        if target_col not in numeric_df.columns:
            return {"error": "Target column must be numeric for correlation-based feature importance"}
        
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return {"error": "Need at least 2 numeric columns for feature importance analysis"}
        
        feature_importance = {}
        
        if method == 'correlation':
            correlations = numeric_df.corr()[target_col].abs().sort_values(ascending=False)
            for col, corr_val in correlations.items():
                if col != target_col:  # Exclude the target itself
                    feature_importance[col] = float(corr_val)
        
        elif method == 'mutual_info':
            try:
                from sklearn.feature_selection import mutual_info_regression
                
                features = [col for col in numeric_df.columns if col != target_col]
                if features:
                    X = numeric_df[features].fillna(numeric_df[features].mean())
                    y = numeric_df[target_col].fillna(numeric_df[target_col].mean())
                    
                    mi_scores = mutual_info_regression(X, y, random_state=42)
                    for i, col in enumerate(features):
                        feature_importance[col] = float(mi_scores[i])
                
            except ImportError:
                return {"error": "scikit-learn not available for mutual information analysis"}
        
        return {
            'method': method,
            'target_column': target_col,
            'feature_importance': feature_importance,
            'ranked_features': sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        }
    
    def outlier_detection_analysis(self, df: pd.DataFrame, method: str = 'iqr') -> Dict[str, Any]:
        """Comprehensive outlier detection."""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return {"error": "No numeric columns found for outlier detection"}
        
        outlier_results = {}
        
        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            
            if method == 'iqr':
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = series[(series < lower_bound) | (series > upper_bound)]
                
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(series))
                outliers = series[z_scores > 3]
            
            elif method == 'modified_zscore':
                median = series.median()
                mad = np.median(np.abs(series - median))
                modified_z_scores = 0.6745 * (series - median) / mad
                outliers = series[np.abs(modified_z_scores) > 3.5]
            
            else:
                raise ValueError(f"Unknown outlier detection method: {method}")
            
            outlier_results[col] = {
                'outlier_count': int(len(outliers)),
                'outlier_percentage': float(len(outliers) / len(series) * 100) if len(series) > 0 else 0,
                'outlier_indices': outliers.index.tolist(),
                'outlier_values': outliers.values.tolist()
            }
        
        return {
            'method': method,
            'outlier_analysis': outlier_results,
            'total_outliers': sum([result['outlier_count'] for result in outlier_results.values()])
        }
    
    def _calculate_entropy(self, series):
        """Calculate entropy of a categorical series."""
        value_counts = series.value_counts()
        probabilities = value_counts / len(series)
        return -(probabilities * np.log2(probabilities)).sum()

# Global instance
analysis_engine = AnalysisEngine()

# Backwards-compatible export expected by app/routes/api/ml_ops.py
statistical_analyzer = analysis_engine
