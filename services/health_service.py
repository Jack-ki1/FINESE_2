"""Health Service Module - Handles data quality and health scoring functionality."""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any
from utils.data_utils import is_numeric_column, is_categorical_column, is_datetime_column

logger = logging.getLogger(__name__)

def calculate_data_health_score(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate a comprehensive health score for the dataset.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary containing health score and details
    """
    if df is None or df.empty:
        logger.warning("Empty or None DataFrame provided for health scoring")
        return {
            "final_score": 0,
            "details": {
                "completeness": 0,
                "consistency": 0,
                "accuracy": 0,
                "uniqueness": 0,
                "timeliness": 0
            }
        }

    # Calculate individual metrics
    completeness = calculate_completeness_score(df)
    consistency = calculate_consistency_score(df)
    uniqueness = calculate_uniqueness_score(df)
    
    # For accuracy and timeliness, we'll use defaults since they require domain knowledge
    accuracy = 90  # Default high score as it's domain-dependent
    timeliness = 90  # Default high score as it's date-dependent

    # Calculate final score as weighted average
    final_score = round(
        0.3 * completeness +
        0.25 * consistency +
        0.2 * uniqueness +
        0.15 * accuracy +
        0.1 * timeliness
    )

    return {
        "final_score": final_score,
        "details": {
            "completeness": completeness,
            "consistency": consistency,
            "accuracy": accuracy,
            "uniqueness": uniqueness,
            "timeliness": timeliness
        }
    }


def calculate_completeness_score(df: pd.DataFrame) -> float:
    """Calculate completeness score based on missing values."""
    if df.empty:
        return 0.0
    
    total_cells = df.shape[0] * df.shape[1]
    if total_cells == 0:
        return 0.0
        
    missing_cells = df.isnull().sum().sum()
    completeness = ((total_cells - missing_cells) / total_cells) * 100
    return min(100.0, max(0.0, completeness))


def calculate_consistency_score(df: pd.DataFrame) -> float:
    """Calculate consistency score based on data types and patterns."""
    if df.empty:
        return 0.0

    if len(df.columns) == 0:
        return 100.0

    # Calculate consistency based on data types
    consistent_cols = 0
    for col in df.columns:
        if is_numeric_column(df[col]):
            consistent_cols += 1
        elif is_categorical_column(df[col]):
            consistent_cols += 1
        elif is_datetime_column(df[col]):
            consistent_cols += 1
        # Add more consistency checks as needed

    consistency = (consistent_cols / len(df.columns)) * 100
    return min(100.0, max(0.0, consistency))


def calculate_uniqueness_score(df: pd.DataFrame) -> float:
    """Calculate uniqueness score based on duplicate rows."""
    if df.empty or len(df.columns) == 0:
        return 0.0

    unique_rows = len(df.drop_duplicates())
    total_rows = len(df)
    
    if total_rows == 0:
        return 100.0
        
    uniqueness = (unique_rows / total_rows) * 100
    return min(100.0, max(0.0, uniqueness))


def generate_health_insights(df: pd.DataFrame) -> List[str]:
    """
    Generate insights about the health of the dataset.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of insights as strings
    """
    insights = []
    
    if df is None or df.empty:
        return insights

    # Missing values insights
    missing = df.isnull().sum()
    high_miss_cols = missing[missing > len(df) * 0.3].index.tolist()
    if high_miss_cols:
        insights.append(f"⚠️ **Critical Missing Values**: `{', '.join(high_miss_cols)}` (>30% missing)")

    # Data type insights
    obj_cols = [col for col in df.columns if is_categorical_column(df[col])]
    for col in obj_cols:
        sample = df[col].dropna().astype(str)
        if sample.str.contains(r'[$€£¥]', na=False).any():
            insights.append(f"⚠️ **Inconsistent formatting in `{col}`**: Contains currency symbols")
        if sample.str.contains(r'[,\s]{2,}', na=False).any():
            insights.append(f"⚠️ **Inconsistent formatting in `{col}`**: Extra commas or whitespace detected")

    # Duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        insights.append(f"⚠️ **Duplicates**: {dup_count:,} duplicate row(s) found")

    # Date column analysis
    date_cols = [col for col in df.columns if is_datetime_column(df[col])]
    for col in date_cols:
        try:
            dates = pd.to_datetime(df[col], errors='coerce').dropna()
            if len(dates) < 2:
                continue
            gaps = dates.diff().dt.days.dropna()
            if len(gaps) > 0:
                median_gap = gaps.median()
                if median_gap > 7:
                    insights.append(f"⚠️ **Irregular sampling in `{col}`**: Median gap = {median_gap:.0f} days")
        except Exception as e:
            logger.debug(f"Could not analyze date column {col}: {e}")

    # High cardinality
    for col in df.columns:
        n_unique = df[col].nunique()
        n_total = len(df)
        if n_unique > 10 and (n_unique / n_total) > 0.95:
            insights.append(f"💡 **High cardinality in `{col}`**: {n_unique}/{n_total} unique values — consider label encoding or binning")

    # Skewness
    num_cols = [col for col in df.columns if is_numeric_column(df[col])]
    for col in num_cols:
        skew = df[col].skew()
        if abs(skew) > 2:
            insights.append(f"⚠️ **Skewed distribution in `{col}`**: Skewness = {skew:.2f} (non-normal)")

    # Zero variance
    zero_var = df.nunique() == 1
    if zero_var.any():
        cols = zero_var[zero_var].index.tolist()
        insights.append(f"⚠️ **Zero variance columns**: `{', '.join(cols)}` — these contain only one value")

    return insights