import pandas as pd
import io
import zipfile
from typing import Dict, Any, Optional
from datetime import datetime
import json

from .dataset_service import DatasetService

class ExportService:
    def __init__(self):
        self.dataset_service = DatasetService()
    
    async def export_dataset(
        self, 
        dataset_id: str, 
        format: str = 'csv', 
        columns: Optional[list] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Export a dataset in the specified format
        """
        df = self.dataset_service.datasets.get(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Apply column selection if specified
        if columns:
            df = df[[col for col in columns if col in df.columns]]
        
        # Apply filters if specified (simplified implementation)
        if filters:
            for col, values in filters.items():
                if col in df.columns:
                    if isinstance(values, list):
                        df = df[df[col].isin(values)]
                    else:
                        df = df[df[col] == values]
        
        buffer = io.BytesIO()
        
        if format.lower() == 'csv':
            df.to_csv(buffer, index=False)
        elif format.lower() == 'excel':
            df.to_excel(buffer, index=False, engine='openpyxl')
        elif format.lower() == 'json':
            df.to_json(buffer, orient='records', date_format='iso')
        elif format.lower() == 'parquet':
            df.to_parquet(buffer, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        buffer.seek(0)
        return buffer.getvalue()
    
    async def export_report(
        self,
        dataset_id: str,
        report_type: str = 'summary',
        include_visualizations: bool = True
    ) -> bytes:
        """
        Export a report about the dataset
        """
        # Get dataset summary
        summary = await self.dataset_service.get_dataset_summary(dataset_id)
        
        # In a real implementation, this would generate a full report with visualizations
        # For now, we'll create a simple JSON report
        
        report_data = {
            "dataset_id": dataset_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "name": summary.name,
                "shape": summary.shape,
                "size_mb": summary.size_mb,
                "created_at": summary.created_at.isoformat(),
                "columns": [
                    {
                        "name": col.name,
                        "dtype": col.dtype,
                        "missing_count": col.missing_count,
                        "missing_percentage": col.missing_percentage,
                        "unique_count": col.unique_count
                    } for col in summary.columns
                ]
            }
        }
        
        buffer = io.BytesIO()
        json.dump(report_data, buffer, indent=2)
        buffer.seek(0)
        return buffer.getvalue()
    
    async def export_bundle(
        self,
        dataset_id: str,
        formats: list = ['csv'],
        include_report: bool = True
    ) -> bytes:
        """
        Export a bundle with multiple formats and optionally a report
        """
        df = self.dataset_service.datasets.get(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Export in each requested format
            for fmt in formats:
                try:
                    export_data = await self.export_dataset(dataset_id, format=fmt)
                    
                    # Create appropriate filename based on format
                    if fmt == 'csv':
                        filename = f"{dataset_id}.csv"
                    elif fmt == 'excel':
                        filename = f"{dataset_id}.xlsx"
                    elif fmt == 'json':
                        filename = f"{dataset_id}.json"
                    elif fmt == 'parquet':
                        filename = f"{dataset_id}.parquet"
                    else:
                        filename = f"{dataset_id}.{fmt}"
                    
                    zip_file.writestr(filename, export_data)
                except Exception as e:
                    # If a specific format fails, continue with others
                    print(f"Warning: Could not export {fmt} format: {str(e)}")
            
            # Add report if requested
            if include_report:
                try:
                    report_data = await self.export_report(dataset_id)
                    zip_file.writestr(f"{dataset_id}_report.json", report_data)
                except Exception as e:
                    print(f"Warning: Could not generate report: {str(e)}")
        
        buffer.seek(0)
        return buffer.getvalue()