import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from ..schemas.health import HealthScorecard, HealthCategory
from .dataset_service import DatasetService
from .cache_service import CacheService

class HealthService:
    def __init__(self):
        self.dataset_service = DatasetService()
        self.cache_service = CacheService()

    async def get_cached_health_score(self, dataset_id: str) -> Optional[HealthScorecard]:
        """Get cached health score if it exists"""
        return await self.cache_service.get_health_score(dataset_id)

    async def cache_health_score(self, dataset_id: str, health_scorecard: HealthScorecard):
        """Cache health score"""
        await self.cache_service.cache_health_score(dataset_id, health_scorecard)

    async def calculate_health_score(self, dataset_id: str) -> HealthScorecard:
        """Calculate comprehensive health score for a dataset"""
        # Get the dataset
        df = self.dataset_service.datasets.get(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Calculate individual health metrics
        completeness_score = self._calculate_completeness_score(df)
        consistency_score = self._calculate_consistency_score(df)
        accuracy_score = self._calculate_accuracy_score(df)
        uniqueness_score = self._calculate_uniqueness_score(df)
        timeliness_score = self._calculate_timeliness_score(df)
        
        # Calculate final weighted score (equal weights for now)
        final_score = (
            completeness_score * 0.2 +
            consistency_score * 0.2 +
            accuracy_score * 0.2 +
            uniqueness_score * 0.2 +
            timeliness_score * 0.2
        )
        
        # Generate diagnostics and recommendations
        diagnostics = await self.generate_diagnostics(dataset_id)
        recommendations = await self._generate_recommendations(df, diagnostics)
        
        health_scorecard = HealthScorecard(
            final_score=round(final_score, 2),
            details={
                HealthCategory.COMPLETENESS: round(completeness_score, 2),
                HealthCategory.CONSISTENCY: round(consistency_score, 2),
                HealthCategory.ACCURACY: round(accuracy_score, 2),
                HealthCategory.UNIQUENESS: round(uniqueness_score, 2),
                HealthCategory.TIMELINESS: round(timeliness_score, 2),
            },
            diagnostics=diagnostics,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
        
        return health_scorecard

    def _calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """Calculate completeness score based on missing values"""
        total_cells = df.size
        if total_cells == 0:
            return 100.0
        
        missing_cells = df.isnull().sum().sum()
        completeness_ratio = (total_cells - missing_cells) / total_cells
        return completeness_ratio * 100

    def _calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """Calculate consistency score based on data types and formats"""
        if df.empty:
            return 100.0
            
        consistency_issues = 0
        total_checks = 0
        
        for col in df.columns:
            total_checks += 1
            
            # Check for mixed data types in object columns
            if df[col].dtype == 'object':
                non_null_values = df[col].dropna()
                if len(non_null_values) > 0:
                    # Try to infer if the column should be numeric
                    try:
                        pd.to_numeric(non_null_values)
                        # If successful, check for non-numeric values in a sample
                        sample_non_numeric = non_null_values.apply(
                            lambda x: not str(x).replace('.', '').replace('-', '').isdigit()
                        ).sum()
                        if sample_non_numeric > len(non_null_values) * 0.1:  # More than 10% non-numeric
                            consistency_issues += 1
                    except:
                        # Column contains truly mixed types
                        consistency_issues += 1
            # For numeric columns, check for outliers
            elif pd.api.types.is_numeric_dtype(df[col]):
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                outlier_ratio = outliers / len(df[col])
                if outlier_ratio > 0.1:  # More than 10% outliers
                    consistency_issues += 1
        
        if total_checks == 0:
            return 100.0
            
        consistency_ratio = (total_checks - consistency_issues) / total_checks
        return consistency_ratio * 100

    def _calculate_accuracy_score(self, df: pd.DataFrame) -> float:
        """Calculate accuracy score based on data validity"""
        if df.empty:
            return 100.0
            
        accuracy_issues = 0
        total_checks = 0
        
        for col in df.columns:
            total_checks += 1
            
            # For numeric columns, check for invalid values
            if pd.api.types.is_numeric_dtype(df[col]):
                invalid_values = df[col].isna().sum() + (df[col].isinf().sum() if df[col].dtype.kind in 'fc' else 0)
                if invalid_values > len(df) * 0.1:  # More than 10% invalid
                    accuracy_issues += 1
            # For date columns, check for invalid dates
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                invalid_dates = df[col].isna().sum()
                if invalid_dates > len(df) * 0.1:
                    accuracy_issues += 1
        
        if total_checks == 0:
            return 100.0
            
        accuracy_ratio = (total_checks - accuracy_issues) / total_checks
        return accuracy_ratio * 100

    def _calculate_uniqueness_score(self, df: pd.DataFrame) -> float:
        """Calculate uniqueness score based on duplicate records"""
        if df.empty:
            return 100.0
            
        total_records = len(df)
        duplicate_records = df.duplicated().sum()
        
        unique_ratio = (total_records - duplicate_records) / total_records
        return unique_ratio * 100

    def _calculate_timeliness_score(self, df: pd.DataFrame) -> float:
        """Calculate timeliness score based on recent data availability"""
        if df.empty:
            return 0.0
            
        # Look for potential date columns
        date_cols = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_cols.append(col)
            else:
                # Try to parse as date
                try:
                    sample = df[col].dropna().head(100)  # Sample to improve performance
                    pd.to_datetime(sample, errors='raise', infer_datetime_format=True)
                    date_cols.append(col)
                except:
                    continue
        
        if not date_cols:
            # If no date columns, assume perfect timeliness
            return 100.0
        
        # Use the first date column found
        date_col = date_cols[0]
        date_series = pd.to_datetime(df[date_col], errors='coerce').dropna()
        
        if len(date_series) == 0:
            return 0.0
        
        # Calculate time since most recent record
        max_date = date_series.max()
        days_since_recent = (datetime.now() - max_date).days
        
        # Score based on recency (recent data gets higher score)
        # Scale: data from today=100, data from 30 days ago=70, data from 365 days ago=30
        if days_since_recent <= 30:
            timeliness_score = max(70, 100 - (days_since_recent / 30) * 30)
        else:
            # For older data, use logarithmic scale
            timeliness_score = max(10, 70 - (np.log10(days_since_recent / 30) * 20))
        
        return timeliness_score

    async def generate_diagnostics(self, dataset_id: str) -> Dict[str, Any]:
        """Generate detailed diagnostics for the dataset"""
        df = self.dataset_service.datasets.get(dataset_id)
        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        diagnostics = {
            "shape": df.shape,
            "memory_usage": df.memory_usage(deep=True).sum(),
            "dtypes_summary": df.dtypes.value_counts().to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_columns": [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])],
            "categorical_columns": [col for col in df.columns if pd.api.types.is_object_dtype(df[col])],
            "date_columns": [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        }
        
        # Add statistical summary for numeric columns
        numeric_cols = diagnostics["numeric_columns"]
        if numeric_cols:
            diagnostics["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        return diagnostics

    async def _generate_recommendations(self, df: pd.DataFrame, diagnostics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on data quality issues"""
        recommendations = []
        
        # Missing values recommendations
        missing = df.isnull().sum()
        high_missing_cols = missing[missing > len(df) * 0.5].index.tolist()  # >50% missing
        if high_missing_cols:
            recommendations.append(f"Consider dropping columns with high missing values: {', '.join(high_missing_cols)}")
        
        # Duplicate records recommendation
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            recommendations.append(f"Remove {duplicates} duplicate rows to improve uniqueness")
        
        # Data type recommendations
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    pd.to_numeric(df[col].dropna())
                    recommendations.append(f"Convert column '{col}' to numeric type")
                except:
                    pass
                
                # Check for high cardinality
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio > 0.9:  # High cardinality
                    recommendations.append(f"Column '{col}' has high cardinality - consider if it's useful for analysis")
        
        # Outlier recommendations
        for col in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            outlier_ratio = outliers / len(df)
            if outlier_ratio > 0.05:  # More than 5% outliers
                recommendations.append(f"Column '{col}' has {outlier_ratio:.2%} outliers - consider treatment")
        
        if not recommendations:
            recommendations.append("Your data looks clean! No major issues detected.")
        
        return recommendations