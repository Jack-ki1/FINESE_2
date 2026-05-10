import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime

from ..schemas.charts import ChartPayload
from .dataset_service import DatasetService
from .cache_service import CacheService

class ChartService:
    def __init__(self):
        self.dataset_service = DatasetService()
        self.cache_service = CacheService()

    async def get_cached_chart_data(self, chart_key: str) -> Optional[ChartPayload]:
        """Get cached chart data if it exists"""
        return await self.cache_service.get_chart_data(chart_key)

    async def cache_chart_data(self, chart_key: str, chart_payload: ChartPayload):
        """Cache chart data"""
        await self.cache_service.cache_chart_data(chart_key, chart_payload)

    async def generate_chart(
        self,
        dataset_id: str,
        chart_type: str,
        x_axis: str,
        y_axis: Optional[str] = None,
        group_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ChartPayload:
        """Generate chart data based on parameters"""
        # Get the dataset
        df = self.dataset_service.datasets.get(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Apply filters if provided
        if filters:
            # This is a simplified implementation - in reality you'd have more sophisticated filtering
            for col, values in filters.items():
                if col in df.columns:
                    if isinstance(values, list):
                        df = df[df[col].isin(values)]
                    else:
                        df = df[df[col] == values]
        
        # Generate chart data based on chart type
        if chart_type == "bar":
            chart_data = await self._generate_bar_chart_data(df, x_axis, y_axis, group_by)
            title = f"Bar Chart: {x_axis} vs {y_axis or 'Count'}"
        elif chart_type == "line":
            chart_data = await self._generate_line_chart_data(df, x_axis, y_axis, group_by)
            title = f"Line Chart: {x_axis} vs {y_axis}"
        elif chart_type == "scatter":
            if y_axis is None:
                raise ValueError("Scatter plots require both x and y axes")
            chart_data = await self._generate_scatter_plot_data(df, x_axis, y_axis, group_by)
            title = f"Scatter Plot: {x_axis} vs {y_axis}"
        elif chart_type == "histogram":
            chart_data = await self._generate_histogram_data(df, x_axis, group_by)
            title = f"Histogram: Distribution of {x_axis}"
        elif chart_type == "heatmap":
            chart_data = await self._generate_heatmap_data(df, x_axis, y_axis)
            title = f"Heatmap: {x_axis} vs {y_axis}"
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # Create and return the payload
        return ChartPayload(
            chart_type=chart_type,
            title=title,
            data=chart_data,
            x_axis_label=x_axis,
            y_axis_label=y_axis,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "dataset_id": dataset_id,
                "group_by": group_by
            }
        )

    async def _generate_bar_chart_data(
        self, 
        df: pd.DataFrame, 
        x_axis: str, 
        y_axis: Optional[str] = None, 
        group_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate data for bar charts"""
        if y_axis:
            # Group by x-axis and aggregate y-axis
            if group_by:
                grouped = df.groupby([x_axis, group_by])[y_axis].sum().reset_index()
                # Transform to list of dicts
                result = []
                for _, row in grouped.iterrows():
                    result.append({
                        x_axis: row[x_axis],
                        y_axis: row[y_axis],
                        group_by: row[group_by]
                    })
            else:
                grouped = df.groupby(x_axis)[y_axis].sum().reset_index()
                result = grouped.to_dict('records')
        else:
            # Count occurrences of each x value
            value_counts = df[x_axis].value_counts().reset_index()
            value_counts.columns = [x_axis, 'count']
            result = value_counts.to_dict('records')
        
        return result

    async def _generate_line_chart_data(
        self, 
        df: pd.DataFrame, 
        x_axis: str, 
        y_axis: str, 
        group_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate data for line charts"""
        if group_by:
            grouped = df.groupby([x_axis, group_by])[y_axis].mean().reset_index()
            result = []
            for _, row in grouped.iterrows():
                result.append({
                    x_axis: row[x_axis],
                    y_axis: row[y_axis],
                    group_by: row[group_by]
                })
        else:
            grouped = df.groupby(x_axis)[y_axis].mean().reset_index()
            result = grouped.to_dict('records')
        
        return result

    async def _generate_scatter_plot_data(
        self, 
        df: pd.DataFrame, 
        x_axis: str, 
        y_axis: str, 
        group_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate data for scatter plots"""
        columns_to_select = [x_axis, y_axis]
        if group_by:
            columns_to_select.append(group_by)
        
        result = df[columns_to_select].dropna().to_dict('records')
        return result

    async def _generate_histogram_data(
        self, 
        df: pd.DataFrame, 
        x_axis: str, 
        group_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate data for histograms"""
        # Simplified histogram - in practice, you'd want more sophisticated binning
        values = df[x_axis].dropna()
        
        # Create bins
        if pd.api.types.is_numeric_dtype(values):
            bins = min(20, len(values.unique()))
            hist, bin_edges = np.histogram(values, bins=bins)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            result = [
                {"bin_center": float(center), "count": int(count)}
                for center, count in zip(bin_centers, hist)
            ]
        else:
            # For categorical data, just count occurrences
            value_counts = values.value_counts()
            result = [
                {"category": str(idx), "count": int(count)}
                for idx, count in value_counts.items()
            ]
        
        return result

    async def _generate_heatmap_data(
        self, 
        df: pd.DataFrame, 
        x_axis: str, 
        y_axis: str
    ) -> List[Dict[str, Any]]:
        """Generate data for heatmaps"""
        if not (pd.api.types.is_numeric_dtype(df[x_axis]) and pd.api.types.is_numeric_dtype(df[y_axis])):
            # For non-numeric data, create a crosstab
            crosstab = pd.crosstab(df[x_axis], df[y_axis])
        else:
            # For numeric data, group into bins first
            x_bins = pd.cut(df[x_axis], bins=min(10, df[x_axis].nunique()))
            y_bins = pd.cut(df[y_axis], bins=min(10, df[y_axis].nunique()))
            crosstab = pd.crosstab(x_bins, y_bins)
        
        result = []
        for x_val, row in crosstab.iterrows():
            for y_val, count in row.items():
                result.append({
                    "x": str(x_val),
                    "y": str(y_val),
                    "value": int(count)
                })
        
        return result

    async def get_column_info_for_charting(self, dataset_id: str) -> List[Dict[str, str]]:
        """Get information about columns suitable for charting"""
        df = self.dataset_service.datasets.get(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        columns_info = []
        for col in df.columns:
            col_info = {
                "name": col,
                "type": str(df[col].dtype),
                "suggest_as": []
            }
            
            # Determine appropriate chart types for this column
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info["suggest_as"].extend(["x_axis", "y_axis", "size", "color"])
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_info["suggest_as"].extend(["x_axis", "time_series"])
            else:
                col_info["suggest_as"].extend(["x_axis", "group_by", "filter"])
            
            columns_info.append(col_info)
        
        return columns_info