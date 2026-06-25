"""Cleaning Service Module - Handles data cleaning and preprocessing functionality."""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Tuple
from utils.data_utils import is_numeric_column, is_categorical_column, is_datetime_column
from utils.data_utils import safe_convert_type

logger = logging.getLogger(__name__)

def get_cleaning_suggestions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate cleaning suggestions for the given DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of dictionaries containing cleaning suggestions
    """
    suggestions = []
    
    if df is None or df.empty:
        return suggestions

    # Missing values analysis
    missing = df.isnull().sum()
    high_miss = missing[missing > len(df) * 0.3]
    for col in high_miss.index:
        suggestions.append({
            "column": col,
            "issue": f"Missing values: {missing[col]} ({(missing[col]/len(df)*100):.1f}%)",
            "recommendation": "Drop column or impute with median/mean",
            "severity": "🔴 Critical"
        })

    # Check for columns with numeric characters but stored as text
    for col in [c for c in df.columns if is_categorical_column(df[c])]:
        cleaned = df[col].astype(str).str.replace(r'[^\d\.-]', '', regex=True)
        if cleaned.str.match(r'^-?\d*\.?\d*$').any():
            if not (df[col].nunique() / len(df) > 0.95):
                suggestions.append({
                    "column": col,
                    "issue": "Contains numeric characters but stored as text",
                    "recommendation": "Convert to numeric using `pd.to_numeric(..., errors='coerce')`",
                    "severity": "🟡 Medium"
                })

    # Check for inconsistent labels due to case/whitespace
    for col in [c for c in df.columns if is_categorical_column(df[c])]:
        original_nunique = df[col].nunique()
        normalized = df[col].astype(str).str.strip().str.lower()
        normalized_nunique = normalized.nunique()
        if normalized_nunique < original_nunique:
            diff = original_nunique - normalized_nunique
            suggestions.append({
                "column": col,
                "issue": f"{diff} inconsistent labels due to case/whitespace",
                "recommendation": "Normalize case and trim whitespace",
                "severity": "🟡 Low"
            })

    # Check for negative values in columns that shouldn't have them
    for col in [c for c in df.columns if is_numeric_column(df[c])]:
        if (df[col] < 0).sum() > 0:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['price', 'cost', 'amount', 'fee', 'age', 'year']):
                suggestions.append({
                    "column": col,
                    "issue": f"{(df[col] < 0).sum()} negative values detected",
                    "recommendation": "Review for data entry errors (e.g., negative prices/ages)",
                    "severity": "🔴 Critical"
                })

    # Check for duplicate column names
    duplicates = df.columns[df.columns.duplicated()]
    if len(duplicates) > 0:
        dup_list = ', '.join(set(duplicates))
        suggestions.append({
            "column": "",
            "issue": f"Duplicate column names: {dup_list}",
            "recommendation": "Rename or remove duplicate columns to avoid ambiguity",
            "severity": "🔴 Critical"
        })

    # Check for zero variance columns
    zero_var = df.nunique() == 1
    if zero_var.any():
        cols = zero_var[zero_var].index.tolist()
        suggestions.append({
            "column": ", ".join(cols),
            "issue": "One or more columns have only one unique value",
            "recommendation": "Remove these columns — they add no predictive value",
            "severity": "🟡 Low"
        })

    # Check for date-like text columns
    for col in [c for c in df.columns if is_categorical_column(df[c])]:
        sample = df[col].dropna().head(10).astype(str)
        date_patterns = [r'\d{4}-\d{1,2}-\d{1,2}', r'\d{1,2}/\d{1,2}/\d{4}', r'\d{1,2}-\d{1,2}-\d{4}']
        if any(sample.str.contains(p, na=False, regex=True).any() for p in date_patterns):
            suggestions.append({
                "column": col,
                "issue": "Looks like a date but stored as text",
                "recommendation": "Convert to datetime using `pd.to_datetime()`",
                "severity": "🟡 Medium"
            })

    return suggestions


def apply_cleaning_suggestions(df: pd.DataFrame, suggestions: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Apply cleaning suggestions to the DataFrame.
    
    Args:
        df: Input DataFrame
        suggestions: List of cleaning suggestions to apply
        
    Returns:
        Tuple of (cleaned DataFrame, list of applied changes)
    """
    tmp = df.copy()
    changes_log = []
    
    for suggestion in suggestions:
        col = suggestion["column"]
        rec = suggestion["recommendation"]
        
        if "Convert to numeric" in rec and col and col in tmp.columns:
            try:
                tmp[col] = pd.to_numeric(tmp[col], errors='coerce')
                changes_log.append(f"✅ Converted `{col}` to numeric")
            except Exception as e:
                logger.warning(f"Failed to convert {col} to numeric: {e}")
                changes_log.append(f"❌ Failed to convert `{col}` to numeric: {e}")
        elif "Normalize case" in rec and col and col in tmp.columns:
            try:
                tmp[col] = tmp[col].astype(str).str.strip().str.lower()
                changes_log.append(f"✅ Normalized case & whitespace in `{col}`")
            except Exception as e:
                logger.warning(f"Failed to normalize {col}: {e}")
                changes_log.append(f"❌ Failed to normalize `{col}`: {e}")
        elif "Drop column" in rec and col and col in tmp.columns:
            try:
                tmp = tmp.drop(columns=[col])
                changes_log.append(f"❌ Dropped column `{col}`")
            except Exception as e:
                logger.warning(f"Failed to drop {col}: {e}")
                changes_log.append(f"❌ Failed to drop `{col}`: {e}")
        elif "Convert to datetime" in rec and col and col in tmp.columns:
            try:
                tmp[col] = pd.to_datetime(tmp[col], errors='coerce')
                changes_log.append(f"✅ Converted `{col}` to datetime")
            except Exception as e:
                logger.warning(f"Failed to convert {col} to datetime: {e}")
                changes_log.append(f"❌ Failed to convert `{col}` to datetime: {e}")
    
    return tmp, changes_log


def suggest_optimal_type(series: pd.Series, col_name: str) -> str:
    """
    Suggest optimal data type based on series content.
    
    Args:
        series: Pandas Series to analyze
        col_name: Name of the column
        
    Returns:
        Suggested data type as string
    """
    import pandas as pd
    
    current_type = str(series.dtype)
    
    # If already a specific type, keep it
    if current_type in ["int64", "float64", "object", "datetime64[ns]", "bool", "category", "string", "Int64", "Float64", "boolean"]:
        return current_type
    
    # For object types, analyze content
    if current_type == 'object':
        sample = series.dropna().head(1000)
        if len(sample) == 0:
            return 'object'
            
        str_sample = sample.astype(str)
        
        # Check for boolean-like values using vectorized operations
        bool_mask = str_sample.str.lower().isin(['true','false','yes','no','1','0'])
        if bool_mask.mean() > 0.9:
            return 'bool'
            
        # Check for numeric values using vectorized operations
        numeric_ratio = pd.to_numeric(sample, errors='coerce').notna().mean()
        if numeric_ratio > 0.9:
            # Check if they are integers
            numeric_series = pd.to_numeric(sample, errors='coerce').dropna()
            is_integer = (numeric_series % 1 == 0).mean()
            if is_integer > 0.9:
                return 'int64'
            else:
                return 'float64'
                
        # Check for datetime using vectorized operations
        date_ratio = pd.to_datetime(sample, errors='coerce', infer_datetime_format=True).notna().mean()
        if date_ratio > 0.7:
            return 'datetime64[ns]'
            
    return current_type


def convert_column_type(df: pd.DataFrame, col: str, target_type: str) -> pd.DataFrame:
    """
    Convert a column to the specified type.
    
    Args:
        df: Input DataFrame
        col: Column name to convert
        target_type: Target type to convert to
        
    Returns:
        DataFrame with converted column
    """
    df_copy = df.copy()
    
    try:
        df_copy[col] = safe_convert_type(df_copy[col], target_type)
        logger.info(f"Successfully converted {col} to {target_type}")
    except Exception as e:
        logger.error(f"Failed to convert {col} to {target_type}: {e}")
        raise
    
    return df_copy