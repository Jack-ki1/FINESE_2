"""
Helper functions for the FINESE2 application.
"""
from functools import wraps
from flask import current_app, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError


def jwt_optional_dev(f):
    """
    Decorator that makes JWT optional in development mode but required in production.
    In development, if no JWT is present, it sets a default user ID.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if we're in development mode
        is_development = current_app.config.get('ENVIRONMENT', 'development') == 'development' or \
                        current_app.config.get('DEBUG', False)
        
        try:
            # Try to verify JWT normally
            verify_jwt_in_request()
            # If successful, get the identity and proceed normally
            user_id = get_jwt_identity()
            request.current_user_id = user_id
        except NoAuthorizationError:
            # If no authorization header is present
            if is_development:
                # In development mode, allow the request to proceed with a default user
                request.current_user_id = 'dev_user'
            else:
                # In production, raise the exception
                raise
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user_id():
    """
    Get the current user ID from JWT token if available.
    In development mode, returns the actual user ID if a valid token is provided,
    otherwise returns 'dev_user'. In production mode, requires a valid token.
    """
    # Check if we're in development mode
    app_env = current_app.config.get('ENVIRONMENT', 'development')
    is_debug = current_app.config.get('DEBUG', False)
    
    if app_env == 'development' or is_debug:
        # In development mode, check if a token is present in the request
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # There's a token, try to decode it
            try:
                user_id = get_jwt_identity()
                return user_id
            except NoAuthorizationError:
                # If token is invalid, return default user for development
                return 'dev_user'
        else:
            # No token provided in development, return default
            return 'dev_user'
    else:
        # In production mode, require JWT token
        try:
            user_id = get_jwt_identity()
            return user_id
        except NoAuthorizationError:
            # Re-raise the exception in production
            raise


def is_development_mode():
    """
    Check if the application is running in development mode.
    """
    app_env = current_app.config.get('ENVIRONMENT', 'development')
    is_debug = current_app.config.get('DEBUG', False)
    return app_env == 'development' or is_debug


"""
Helper Utilities for data_all1
"""
import base64
import io
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np
import streamlit as st

def get_file_hash(file_bytes: bytes) -> str:
    """Generate a hash for file deduplication."""
    return hashlib.md5(file_bytes).hexdigest()[:12]

def df_to_csv_download_link(df: pd.DataFrame, filename: str = "data.csv") -> str:
    """Generate a download link for a dataframe."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="text-decoration:none;"><button style="background:#00D4AA;color:#0E1117;padding:8px 16px;border:none;border-radius:8px;cursor:pointer;font-weight:600;">📥 Download CSV</button></a>'

def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    """Convert dataframe to Excel bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        # Auto-adjust columns
        worksheet = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(str(col))) + 2
            worksheet.set_column(i, i, min(max_len, 50))
    return output.getvalue()

def infer_problem_type(df: pd.DataFrame, target_col: str) -> str:
    """Infer whether a problem is regression or classification."""
    if target_col not in df.columns:
        return "unknown"

    target = df[target_col].dropna()

    if target.dtype == 'object' or target.dtype.name == 'category':
        return "classification"

    if target.nunique() <= 10 and target.nunique() / len(target) < 0.05:
        return "classification"

    return "regression"

def get_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Categorize columns by type."""
    result = {
        "numeric": [],
        "categorical": [],
        "datetime": [],
        "text": [],
        "boolean": [],
        "id": []
    }

    for col in df.columns:
        dtype = df[col].dtype
        unique_ratio = df[col].nunique() / len(df) if len(df) > 0 else 0

        if pd.api.types.is_bool_dtype(dtype):
            result["boolean"].append(col)
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            result["datetime"].append(col)
        elif pd.api.types.is_numeric_dtype(dtype):
            if unique_ratio > 0.95 and df[col].nunique() == len(df):
                result["id"].append(col)
            else:
                result["numeric"].append(col)
        else:
            if df[col].nunique() <= 20 or unique_ratio < 0.05:
                result["categorical"].append(col)
            else:
                result["text"].append(col)

    return result

def summarize_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a comprehensive summary of a dataframe."""
    if df is None or df.empty:
        return {}

    col_types = get_column_types(df)

    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "memory_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        "missing_cells": df.isnull().sum().sum(),
        "missing_pct": (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100,
        "duplicate_rows": df.duplicated().sum(),
        "numeric_cols": len(col_types["numeric"]),
        "categorical_cols": len(col_types["categorical"]),
        "datetime_cols": len(col_types["datetime"]),
        "text_cols": len(col_types["text"]),
        "column_types": col_types
    }
    return summary

def safe_json_dump(obj: Any) -> str:
    """Safely convert object to JSON string."""
    def default_handler(o):
        if isinstance(o, (np.integer, np.floating)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, pd.Timestamp):
            return o.isoformat()
        return str(o)
    return json.dumps(obj, default=default_handler, indent=2)

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def format_number(n: Union[int, float], decimals: int = 2) -> str:
    """Format number with appropriate suffix."""
    if n is None:
        return "N/A"
    if abs(n) >= 1e9:
        return f"{n/1e9:.{decimals}f}B"
    if abs(n) >= 1e6:
        return f"{n/1e6:.{decimals}f}M"
    if abs(n) >= 1e3:
        return f"{n/1e3:.{decimals}f}K"
    return f"{n:.{decimals}f}"

def get_time_stamp() -> str:
    """Get formatted timestamp."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def get_column_analysis(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """Get detailed analysis for a single column."""
    analysis = {
        "name": col,
        "type": str(df[col].dtype),
        "null_count": int(df[col].isnull().sum()),
        "null_percentage": (df[col].isnull().sum() / len(df)) * 100,
        "unique_count": int(df[col].nunique()),
        "unique_percentage": (df[col].nunique() / len(df)) * 100,
        "min": None,
        "max": None,
        "mean": None,
        "std": None,
        "most_common": None,
        "most_common_count": None,
        "is_target_candidate": False
    }

    if not df[col].isnull().all():
        if pd.api.types.is_numeric_dtype(df[col]):
            analysis["min"] = float(df[col].min())
            analysis["max"] = float(df[col].max())
            analysis["mean"] = float(df[col].mean())
            analysis["std"] = float(df[col].std())
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            analysis["min"] = df[col].min().isoformat() if not pd.isna(df[col].min()) else None
            analysis["max"] = df[col].max().isoformat() if not pd.isna(df[col].max()) else None
        else:
            mode = df[col].mode()
            if not mode.empty:
                analysis["most_common"] = str(mode.iloc[0])
                analysis["most_common_count"] = int(df[col].value_counts().iloc[0])

        # Check if column is a potential target variable
        if df[col].nunique() < len(df) * 0.1:  # Less than 10% unique values
            analysis["is_target_candidate"] = True

    return analysis

def create_data_profile_text(df: pd.DataFrame) -> str:
    """Create a comprehensive textual profile of the dataset for AI context."""
    if df is None or df.empty:
        return "No data loaded."

    summary = summarize_dataframe(df)
    lines = [
        f"DATASET PROFILE:",
        f"- Shape: {summary['rows']:,} rows × {summary['columns']} columns",
        f"- Memory usage: {summary['memory_mb']:.2f} MB",
        f"- Missing values: {summary['missing_cells']:,} cells ({summary['missing_pct']:.1f}%)",
        f"- Duplicate rows: {summary['duplicate_rows']:,} rows",
        "",
        "COLUMN TYPE DISTRIBUTION:",
        f"- Numeric: {len(summary['column_types']['numeric'])}",
        f"- Categorical: {len(summary['column_types']['categorical'])}",
        f"- Datetime: {len(summary['column_types']['datetime'])}",
        f"- Text: {len(summary['column_types']['text'])}",
        f"- Boolean: {len(summary['column_types']['boolean'])}",
        f"- ID-like: {len(summary['column_types']['id'])}",
        "",
        "COLUMN ANALYSIS:"
    ]

    for col in df.columns:
        analysis = get_column_analysis(df, col)
        
        lines.append(f"\n  • {analysis['name']} ({analysis['type']})")
        lines.append(f"    - Null values: {analysis['null_count']} ({analysis['null_percentage']:.1f}%)")
        lines.append(f"    - Unique values: {analysis['unique_count']} ({analysis['unique_percentage']:.1f}%)")
        
        if pd.api.types.is_numeric_dtype(df[col]):
            lines.append(f"    - Range: {analysis['min']:.2f} to {analysis['max']:.2f}")
            lines.append(f"    - Mean ± Std: {analysis['mean']:.2f} ± {analysis['std']:.2f}")
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            lines.append(f"    - Range: {analysis['min']} to {analysis['max']}")
        
        if analysis['most_common']:
            lines.append(f"    - Most common: {analysis['most_common']} ({analysis['most_common_count']} times)")
        
        if analysis['is_target_candidate']:
            lines.append(f"    - Potential target variable")

    # Add numeric statistics
    numeric_cols = summary['column_types']['numeric']
    if numeric_cols:
        lines.append("\nNUMERIC COLUMN STATISTICS:")
        for col in numeric_cols:
            lines.append(f"  • {col}: Skew={df[col].skew():.2f}, Kurtosis={df[col].kurtosis():.2f}")
            if len(numeric_cols) > 3:
                break

    # Add possible target columns
    target_candidates = [col for col in df.columns if get_column_analysis(df, col)['is_target_candidate']]
    if target_candidates:
        lines.append("\nPOSSIBLE TARGET COLUMNS (low cardinality):")
        for col in target_candidates[:5]:  # Limit to top 5
            lines.append(f"  • {col}")

    return "\n".join(lines)
