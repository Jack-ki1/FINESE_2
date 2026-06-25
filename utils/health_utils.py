import streamlit as st
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from .data_utils import get_numeric_columns, get_categorical_columns, get_datetime_columns

logger = logging.getLogger(__name__)

def calculate_data_health_score(df: pd.DataFrame) -> Dict:
    """
    Calculate a comprehensive data health score for a DataFrame
    """
    # Lightweight caching: avoid recomputing across tab switches when data unchanged
    try:
        key = (
            len(df),
            df.shape[1],
            int(df.isnull().sum().sum()),
            int(df.duplicated().sum()),
            int(df.memory_usage(deep=True).sum())
        )
        cached = st.session_state.get('cached_data_health')
        if cached and isinstance(cached, dict) and cached.get('key') == key:
            return cached.get('value')
    except Exception:
        # Fallback to normal computation if any quick metric fails
        pass
    
    total_cols = len(df.columns)
    total_cells = len(df) * total_cols
    missing_cells = df.isnull().sum().sum()
    completeness = max(0, 100 - (missing_cells / total_cells * 100))

    # Improved consistency calculation to prevent negative scores
    consistency = 100
    obj_cols = get_categorical_columns(df)
    if obj_cols:
        for col in obj_cols:
            col_penalty = 0
            series = df[col].astype(str)
            if series.str.contains(r'^\s+|\s+$', regex=True).any():
                col_penalty += 3
            if series.str.contains(r'[A-Z]{2,}').any() and series.str.contains(r'[a-z]').any():
                col_penalty += 2
            if series.str.contains(r'[$€£¥,]', regex=True).any():
                col_penalty += 4
            # Apply penalty but ensure consistency doesn't go below 0
            consistency = max(0, consistency - col_penalty)
    else:
        consistency = 100

    accuracy = 100
    num_cols = get_numeric_columns(df)
    for col in num_cols:
        col_lower = col.lower()
        if any(k in col_lower for k in ['price', 'cost', 'amount', 'fee', 'age', 'year']):
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                accuracy -= min(15, (neg_count / len(df)) * 100)
        if 'age' in col_lower:
            impossible = (df[col] > 150).sum()
            if impossible > 0:
                accuracy -= min(10, (impossible / len(df)) * 100)

    uniqueness = 100
    for col in df.columns:
        ratio = df[col].nunique() / len(df)
        if ratio > 0.95 and df[col].dtype == 'object':
            uniqueness -= 5

    timeliness = 100
    date_cols = get_datetime_columns(df)
    latest_date = None
    if date_cols:
        try:
            d = pd.to_datetime(df[date_cols[0]], errors='coerce').dropna()
            if len(d) > 0:
                latest_date = d.max()
                days_old = (pd.Timestamp.now() - latest_date).days
                if days_old > 365:
                    timeliness -= 20
                elif days_old > 180:
                    timeliness -= 10
        except Exception as e:
            logger.debug(f"Could not parse date column {date_cols[0]}: {e}")

    weights = {"completeness": 0.3, "consistency": 0.25, "accuracy": 0.25, "uniqueness": 0.1, "timeliness": 0.1}
    final_score = (
        completeness * weights["completeness"] +
        consistency * weights["consistency"] +
        accuracy * weights["accuracy"] +
        uniqueness * weights["uniqueness"] +
        timeliness * weights["timeliness"]
    )

    result = {
        "final_score": round(final_score, 1),
        "details": {
            "completeness": round(completeness, 1),
            "consistency": round(consistency, 1),
            "accuracy": round(accuracy, 1),
            "uniqueness": round(uniqueness, 1),
            "timeliness": round(timeliness, 1),
        },
        "weights": weights,
        "metrics": {
            "total_rows": len(df),
            "total_cols": total_cols,
            "missing_cells": missing_cells,
            "missing_pct": round(missing_cells / total_cells * 100, 2),
            "duplicate_rows": int(df.duplicated().sum()),
            "date_col": date_cols[0] if date_cols else None,
            "latest_date": latest_date.isoformat() if latest_date else None,
        }
    }

    # Store in session cache (key computed earlier) when possible
    try:
        st.session_state['cached_data_health'] = {'key': key, 'value': result}
    except Exception:
        pass

    return result

def generate_recommendation_list(df: pd.DataFrame, scorecard: Dict) -> List[str]:
    """Generate a list of recommendations based on the data health scorecard."""
    recommendations = []
    
    # Add recommendations based on scorecard details
    if scorecard['details']['completeness'] < 80:
        missing_cols = df.isnull().sum()
        missing_cols = missing_cols[missing_cols > 0].sort_values(ascending=False)
        if len(missing_cols) > 0:
            top_missing = missing_cols.index[0]
            pct_missing = (missing_cols.iloc[0] / len(df)) * 100
            recommendations.append(f"Fix missing data in '{top_missing}' ({pct_missing:.1f}% missing)")
    
    if scorecard['details']['consistency'] < 80:
        obj_cols = get_categorical_columns(df)
        for col in obj_cols[:3]:  # Check first 3 categorical columns
            series = df[col].astype(str)
            if series.str.contains(r'^\s+|\s+$', regex=True).any():
                count = series.str.contains(r'^\s+|\s+$', regex=True).sum()
                recommendations.append(f"Remove leading/trailing whitespace in '{col}' ({count} instances)")
            if series.str.contains(r'[A-Z]{2,}').any() and series.str.contains(r'[a-z]').any():
                recommendations.append(f"Standardize capitalization in '{col}'")
    
    if scorecard['details']['accuracy'] < 80:
        num_cols = get_numeric_columns(df)
        for col in num_cols[:5]:  # Check first 5 numeric columns
            col_lower = col.lower()
            if any(k in col_lower for k in ['price', 'cost', 'amount', 'fee']):
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    recommendations.append(f"Review negative values in '{col}' ({neg_count} found)")
    
    if scorecard['metrics']['duplicate_rows'] > 0:
        recommendations.append(f"Remove {scorecard['metrics']['duplicate_rows']} duplicate rows")
    
    if scorecard['details']['uniqueness'] < 80:
        for col in df.columns:
            if df[col].nunique() / len(df) > 0.95 and df[col].dtype == 'object':
                recommendations.append(f"Column '{col}' has high cardinality, consider binning or grouping")
    
    # If no specific issues found, provide general recommendations
    if not recommendations:
        recommendations.append("Data quality appears good. Consider adding more data validation rules.")
        recommendations.append("Perform exploratory data analysis to discover hidden patterns.")
    
    return recommendations