import pandas as pd
import duckdb
from typing import Dict, Any, List
import time

from .dataset_service import DatasetService

class SqlService:
    def __init__(self):
        self.dataset_service = DatasetService()
    
    async def execute_query(self, dataset_id: str, query: str) -> pd.DataFrame:
        """
        Execute a SQL query on the specified dataset
        """
        # Get the dataset
        df = self.dataset_service.datasets.get(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Validate and sanitize the query to prevent dangerous operations
        validated_query = self._validate_query(query)
        
        # Register the dataframe in DuckDB
        con = duckdb.connect(':memory:')
        con.register(f"dataset_{dataset_id}", df)
        
        try:
            # Execute the query
            result_df = con.execute(validated_query).fetchdf()
        finally:
            con.close()
        
        return result_df
    
    def _validate_query(self, query: str) -> str:
        """
        Basic query validation to prevent dangerous operations
        """
        query_upper = query.upper().strip()
        
        # Check for potentially dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 
            'GRANT', 'REVOKE', 'TRUNCATE', 'MERGE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        
        # DuckDB doesn't support some SQL features, so we might want to validate against those too
        return query
    
    async def get_dataset_schema(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get the schema of a dataset (columns and types)
        """
        df = self.dataset_service.datasets.get(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        schema = {
            "dataset_id": dataset_id,
            "columns": []
        }
        
        for col_name, dtype in df.dtypes.items():
            schema["columns"].append({
                "name": col_name,
                "type": str(dtype),
                "nullable": df[col_name].isnull().any(),
                "unique_values": int(df[col_name].nunique()),
                "null_count": int(df[col_name].isnull().sum())
            })
        
        return schema