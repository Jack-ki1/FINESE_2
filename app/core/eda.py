"""
FINESE2 - Consolidated EDA Module
Comprehensive Exploratory Data Analysis capabilities in a single module.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler, LabelEncoder
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

class EDAEngine:
    """
    Consolidated EDA engine providing comprehensive data exploration capabilities.
    """
    
    def __init__(self):
        self.df = None
        self.results = {}
    
    def load_data(self, dataframe):
        """Load data for analysis."""
        self.df = dataframe.copy()
        return self
    
    def basic_statistics(self):
        """Generate basic statistics for the dataset."""
        if self.df is None:
            raise ValueError("No data loaded")
        
        stats = {
            'shape': self.df.shape,
            'columns': list(self.df.columns),
            'dtypes': self.df.dtypes.to_dict(),
            'missing_values': self.df.isnull().sum().to_dict(),
            'missing_percentage': (self.df.isnull().sum() / len(self.df) * 100).to_dict(),
            'duplicate_rows': self.df.duplicated().sum(),
            'memory_usage': dict(self.df.memory_usage(deep=True)),
            'numeric_summary': self.df.describe().to_dict() if not self.df.select_dtypes(include=[np.number]).empty else {},
            'categorical_summary': {}
        }
        
        # Categorical columns summary
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            stats['categorical_summary'][col] = {
                'unique_count': self.df[col].nunique(),
                'top_categories': self.df[col].value_counts().head().to_dict(),
                'cardinality': self.df[col].nunique() / len(self.df) * 100
            }
        
        self.results['basic_stats'] = stats
        return stats
    
    def correlation_analysis(self, method='pearson'):
        """Perform correlation analysis."""
        if self.df is None:
            raise ValueError("No data loaded")
        
        # Select numeric columns
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {"error": "No numeric columns found for correlation analysis"}
        
        corr_matrix = numeric_df.corr(method=method)
        
        # Identify high correlation pairs
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:  # High correlation threshold
                    high_corr_pairs.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': corr_val
                    })
        
        results = {
            'correlation_matrix': corr_matrix.to_dict(),
            'high_correlation_pairs': high_corr_pairs,
            'correlation_method': method
        }
        
        self.results['correlation'] = results
        return results
    
    def distribution_analysis(self, column=None):
        """Analyze distribution of specified column or all columns."""
        if self.df is None:
            raise ValueError("No data loaded")
        
        if column:
            if column not in self.df.columns:
                raise ValueError(f"Column '{column}' not found")
            return self._analyze_single_distribution(column)
        else:
            results = {}
            for col in self.df.columns:
                results[col] = self._analyze_single_distribution(col)
            return results
    
    def _analyze_single_distribution(self, column):
        """Analyze distribution of a single column."""
        series = self.df[column]
        
        if pd.api.types.is_numeric_dtype(series):
            # Numeric distribution analysis
            dist_results = {
                'type': 'numeric',
                'stats': {
                    'mean': float(series.mean()) if not series.empty else None,
                    'median': float(series.median()) if not series.empty else None,
                    'std': float(series.std()) if not series.empty else None,
                    'variance': float(series.var()) if not series.empty else None,
                    'skewness': float(series.skew()) if not series.empty else None,
                    'kurtosis': float(series.kurtosis()) if not series.empty else None,
                    'min': float(series.min()) if not series.empty else None,
                    'max': float(series.max()) if not series.empty else None,
                    'q25': float(series.quantile(0.25)) if not series.empty else None,
                    'q75': float(series.quantile(0.75)) if not series.empty else None
                },
                'outliers': self._detect_outliers(series),
                'distribution_type': self._infer_distribution_type(series)
            }
        else:
            # Categorical distribution analysis
            dist_results = {
                'type': 'categorical',
                'unique_count': int(series.nunique()),
                'top_categories': series.value_counts().head(10).to_dict(),
                'entropy': float(self._calculate_entropy(series)),
                'cardinality': float(series.nunique() / len(series) * 100)
            }
        
        return dist_results
    
    def _detect_outliers(self, series, method='iqr'):
        """Detect outliers using various methods."""
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = series[(series < lower_bound) | (series > upper_bound)]
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(series.dropna()))
            outliers = series[z_scores > 3]
        else:
            return []
        
        return {
            'count': len(outliers),
            'indices': outliers.index.tolist(),
            'values': outliers.values.tolist()
        }
    
    def _infer_distribution_type(self, series):
        """Infer the likely distribution type of a series."""
        if len(series.dropna()) < 8:
            return "insufficient_data"
        
        # Shapiro-Wilk test for normality (limited to 5000 samples)
        sample = series.dropna().sample(min(5000, len(series.dropna())), random_state=42)
        _, p_value = stats.shapiro(sample[:5000]) if len(sample) > 3 else (None, 1)
        
        if p_value > 0.05:
            return "normal"
        else:
            # Additional tests for other distributions
            return "non_normal"
    
    def _calculate_entropy(self, series):
        """Calculate entropy of categorical series."""
        value_counts = series.value_counts()
        probabilities = value_counts / len(series)
        return -(probabilities * np.log2(probabilities)).sum()
    
    def missing_values_analysis(self):
        """Comprehensive missing values analysis."""
        if self.df is None:
            raise ValueError("No data loaded")
        
        missing_data = self.df.isnull().sum()
        missing_percent = (missing_data / len(self.df)) * 100
        
        missing_analysis = {
            'total_missing': int(missing_data.sum()),
            'total_missing_percent': float(missing_data.sum() / (len(self.df) * len(self.df.columns)) * 100),
            'by_column': {
                col: {
                    'count': int(missing_data[col]),
                    'percentage': float(missing_percent[col])
                }
                for col in self.df.columns
            },
            'missing_patterns': self._identify_missing_patterns(),
            'missing_correlation': self._analyze_missing_correlation()
        }
        
        self.results['missing_values'] = missing_analysis
        return missing_analysis
    
    def _identify_missing_patterns(self):
        """Identify patterns in missing values."""
        if self.df is None:
            return {}
        
        # Create missing value indicator matrix
        missing_mask = self.df.isnull()
        if missing_mask.empty:
            return {}
        
        # Count occurrences of each missing pattern
        pattern_counts = missing_mask.astype(int).groupby(list(missing_mask.columns)).size()
        
        return {
            'pattern_frequency': pattern_counts.to_dict(),
            'most_common_pattern': pattern_counts.idxmax() if len(pattern_counts) > 0 else None
        }
    
    def _analyze_missing_correlation(self):
        """Analyze correlation between missing values."""
        if self.df is None:
            return {}
        
        missing_df = self.df.isnull().astype(int)
        corr_matrix = missing_df.corr()
        
        # Find highly correlated missingness
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.5:  # Moderate correlation threshold
                    high_corr_pairs.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': corr_val
                    })
        
        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'high_correlation_pairs': high_corr_pairs
        }
    
    def generate_profile_report(self):
        """Generate comprehensive EDA profile report."""
        if self.df is None:
            raise ValueError("No data loaded")
        
        profile = {
            'basic_statistics': self.basic_statistics(),
            'correlation_analysis': self.correlation_analysis(),
            'missing_values_analysis': self.missing_values_analysis(),
            'distributions': self.distribution_analysis(),
            'dataset_overview': {
                'total_rows': len(self.df),
                'total_columns': len(self.df.columns),
                'numeric_columns': len(self.df.select_dtypes(include=[np.number]).columns),
                'categorical_columns': len(self.df.select_dtypes(include=['object', 'category']).columns),
                'datetime_columns': len(self.df.select_dtypes(include=['datetime64']).columns),
                'memory_usage_mb': float(self.df.memory_usage(deep=True).sum() / 1024 / 1024)
            }
        }
        
        return profile
    
    def detect_anomalies(self, contamination=0.1):
        """Detect anomalies using multiple methods."""
        if self.df is None:
            raise ValueError("No data loaded")
        
        # Import only when needed to avoid dependency issues
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.neighbors import LocalOutlierFactor
            
            # Prepare numeric data
            numeric_df = self.df.select_dtypes(include=[np.number]).dropna()
            if numeric_df.empty:
                return {"error": "No numeric data available for anomaly detection"}
            
            # Isolation Forest
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            iso_labels = iso_forest.fit_predict(numeric_df)
            iso_anomalies = numeric_df.index[iso_labels == -1].tolist()
            
            # Local Outlier Factor (for smaller datasets)
            if len(numeric_df) <= 10000:  # LOF can be memory intensive
                lof = LocalOutlierFactor(n_neighbors=min(20, len(numeric_df)-1), contamination=contamination)
                lof_labels = lof.fit_predict(numeric_df)
                lof_anomalies = numeric_df.index[lof_labels == -1].tolist()
            else:
                lof_anomalies = []
            
            anomaly_results = {
                'isolation_forest': {
                    'anomaly_count': len(iso_anomalies),
                    'anomaly_indices': iso_anomalies,
                    'contamination_rate': contamination
                },
                'local_outlier_factor': {
                    'anomaly_count': len(lof_anomalies),
                    'anomaly_indices': lof_anomalies,
                    'contamination_rate': contamination
                },
                'combined': {
                    'total_anomalies': len(set(iso_anomalies + lof_anomalies)),
                    'common_anomalies': list(set(iso_anomalies) & set(lof_anomalies))
                }
            }
            
            return anomaly_results
            
        except ImportError:
            return {"error": "scikit-learn not available for anomaly detection"}
    
    def feature_interactions(self, target_column=None):
        """Analyze interactions between features."""
        if self.df is None:
            raise ValueError("No data loaded")
        
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {"error": "No numeric columns for interaction analysis"}
        
        interactions = {}
        
        if target_column and target_column in numeric_df.columns:
            # Analyze relationship with target variable
            target_series = numeric_df[target_column]
            for col in numeric_df.columns:
                if col != target_column:
                    # Calculate correlation
                    corr = target_series.corr(numeric_df[col])
                    
                    # Calculate mutual information for non-linear relationships
                    try:
                        from sklearn.feature_selection import mutual_info_regression
                        mi_score = mutual_info_regression(
                            numeric_df[[col]], target_series, random_state=42
                        )[0]
                        
                        interactions[f"{col}_with_{target_column}"] = {
                            'linear_correlation': float(corr),
                            'mutual_information': float(mi_score),
                            'relationship_strength': abs(float(corr))
                        }
                    except ImportError:
                        interactions[f"{col}_with_{target_column}"] = {
                            'linear_correlation': float(corr),
                            'mutual_information': None,
                            'relationship_strength': abs(float(corr))
                        }
        else:
            # Pairwise interactions between all numeric features
            for i, col1 in enumerate(numeric_df.columns):
                for j, col2 in enumerate(numeric_df.columns):
                    if i < j:  # Avoid duplicates
                        corr = numeric_df[col1].corr(numeric_df[col2])
                        interactions[f"{col1}_vs_{col2}"] = {
                            'correlation': float(corr),
                            'absolute_correlation': abs(float(corr))
                        }
        
        return interactions

# Global EDA instance
eda_engine = EDAEngine()