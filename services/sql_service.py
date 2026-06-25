"""SQL Service Module - Handles SQL query execution functionality."""

import pandas as pd
import duckdb
import logging
from typing import Dict, Any, Optional, Union
from io import StringIO

logger = logging.getLogger(__name__)

def execute_sql_query(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    Execute a SQL query on the provided DataFrame using DuckDB.
    
    Args:
        df: Input DataFrame
        query: SQL query to execute
        
    Returns:
        Dictionary containing results and metadata
    """
    try:
        # Register the DataFrame in DuckDB
        conn = duckdb.connect(':memory:')
        conn.register('df', df)
        
        # Execute the query
        result = conn.execute(query).fetchdf()
        
        # Close connection
        conn.close()
        
        return {
            'success': True,
            'result': result,
            'row_count': len(result),
            'column_count': len(result.columns),
            'columns': list(result.columns)
        }
    except Exception as e:
        logger.error(f"SQL query execution failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'result': None
        }


def get_table_schema(df: pd.DataFrame) -> str:
    """
    Generate a table schema representation for SQL queries.
    
    Args:
        df: Input DataFrame
        
    Returns:
        String representation of the table schema
    """
    buffer = StringIO()
    df.info(buf=buffer)
    schema_info = buffer.getvalue()
    
    return schema_info


def validate_sql_syntax(query: str) -> bool:
    """
    Basic validation of SQL syntax.
    
    Args:
        query: SQL query to validate
        
    Returns:
        Boolean indicating if syntax appears valid
    """
    query = query.strip().lower()
    
    # Basic checks
    if not query:
        return False
    
    # Check if it starts with a valid SQL command
    valid_starts = ['select', 'with', 'insert', 'update', 'delete', 'create', 'alter', 'drop']
    if not any(query.startswith(cmd) for cmd in valid_starts):
        return False
    
    # More sophisticated validation could be added here
    
    return True