"""Profiling Service Module - Handles data profiling functionality."""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from io import StringIO

logger = logging.getLogger(__name__)

def generate_basic_profile_report(df: pd.DataFrame) -> str:
    """
    Generate a basic profile report for the dataset.
    
    Args:
        df: Input DataFrame
        
    Returns:
        String containing the profile report
    """
    if df.empty:
        return "# Data Profile Report\n\nDataset is empty."

    # Basic information
    report = StringIO()
    report.write("# Data Profile Report\n\n")
    
    # Dataset shape and size
    report.write(f"## Dataset Overview\n")
    report.write(f"- Shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n")
    report.write(f"- Memory usage: {df.memory_usage(deep=True).sum():,} bytes\n\n")
    
    # Data types
    report.write("## Data Types\n")
    dtype_counts = df.dtypes.value_counts()
    for dtype, count in dtype_counts.items():
        report.write(f"- {dtype}: {count} column(s)\n")
    report.write("\n")
    
    # Missing values
    report.write("## Missing Values\n")
    missing_data = df.isnull().sum()
    missing_percent = (missing_data / len(df)) * 100
    missing_df = pd.DataFrame({
        'Column': df.columns,
        'Missing Count': missing_data.values,
        'Missing Percentage': missing_percent.values
    })
    missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values('Missing Count', ascending=False)
    
    if missing_df.empty:
        report.write("- No missing values found.\n")
    else:
        for _, row in missing_df.iterrows():
            report.write(f"- {row['Column']}: {row['Missing Count']:,} ({row['Missing Percentage']:.2f}%)\n")
    report.write("\n")
    
    # Duplicate rows
    duplicate_count = df.duplicated().sum()
    report.write(f"## Duplicate Rows\n")
    report.write(f"- Total duplicates: {duplicate_count:,}\n\n")
    
    # Numerical columns statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        report.write("## Numerical Columns Statistics\n")
        report.write(df[numeric_cols].describe().to_markdown() if hasattr(df[numeric_cols].describe(), 'to_markdown') 
                     else df[numeric_cols].describe().to_string())
        report.write("\n\n")
    
    # Categorical columns summary
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if categorical_cols:
        report.write("## Categorical Columns Summary\n")
        for col in categorical_cols:
            report.write(f"### {col}\n")
            value_counts = df[col].value_counts().head(10)  # Top 10 values
            for value, count in value_counts.items():
                report.write(f"- `{value}`: {count:,} occurrences\n")
            report.write("\n")
    
    return report.getvalue()


def get_column_profiles(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Generate profiles for each column in the dataset.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary mapping column names to their profiles
    """
    from utils.data_utils import is_numeric_column, is_categorical_column, is_datetime_column
    
    profiles = {}
    
    for col in df.columns:
        series = df[col]
        profile = {
            'name': col,
            'dtype': str(series.dtype),
            'total_count': len(series),
            'missing_count': series.isnull().sum(),
            'missing_percentage': (series.isnull().sum() / len(series)) * 100,
            'unique_count': series.nunique(),
            'unique_percentage': (series.nunique() / len(series)) * 100
        }
        
        if is_numeric_column(series):
            profile.update({
                'type_category': 'numeric',
                'min': series.min(),
                'max': series.max(),
                'mean': series.mean(),
                'std': series.std(),
                'q25': series.quantile(0.25),
                'q50': series.quantile(0.50),
                'q75': series.quantile(0.75),
            })
        elif is_categorical_column(series):
            profile.update({
                'type_category': 'categorical',
                'top_value': series.mode().iloc[0] if not series.mode().empty else None,
                'top_value_count': series.value_counts().iloc[0] if len(series.value_counts()) > 0 else 0,
            })
        elif is_datetime_column(series):
            profile.update({
                'type_category': 'datetime',
                'min_date': series.min(),
                'max_date': series.max(),
                'date_range_days': (series.max() - series.min()).days if series.min() and series.max() else 0,
            })
        else:
            profile.update({
                'type_category': 'other',
            })
        
        profiles[col] = profile
    
    return profiles


def check_data_quality_issues(df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, Any]:
    """
    Check for common data quality issues in the dataset.
    
    Args:
        df: Input DataFrame
        threshold: Threshold for considering an issue significant (default 0.5 = 50%)
        
    Returns:
        Dictionary containing identified quality issues
    """
    issues = {
        'high_missing_ratio': [],
        'near_constant': [],
        'duplicates': 0,
        'mixed_types': [],
        'out_of_bounds': [],
        'inconsistent_formatting': []
    }
    
    # Check for high missing ratio
    missing_ratios = df.isnull().sum() / len(df)
    for col, ratio in missing_ratios.items():
        if ratio > threshold:
            issues['high_missing_ratio'].append({
                'column': col,
                'ratio': ratio,
                'count': df[col].isnull().sum()
            })
    
    # Check for near constant columns (low cardinality)
    for col in df.columns:
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio < 0.01 and df[col].nunique() > 1:  # Less than 1% unique values but not constant
            issues['near_constant'].append({
                'column': col,
                'unique_ratio': unique_ratio,
                'unique_count': df[col].nunique()
            })
    
    # Count duplicates
    issues['duplicates'] = df.duplicated().sum()
    
    return issues