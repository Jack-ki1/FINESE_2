"""
FINESE2 - Report Generation Service
Migrates and enhances engine/report_generator.py with user tracking and storage.
"""
from typing import Dict, Any, Optional, List
import io
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from engine.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ReportService:
    """
    Enhanced report generation service with user isolation.
    
    Wraps legacy ReportGenerator while adding:
    - User-specific report history
    - Report metadata tracking
    - Multiple export formats
    - Scheduled reports (future)
    """
    
    def __init__(self):
        self.generator = ReportGenerator()
    
    def generate_report(self, df: pd.DataFrame, report_type: str,
                       params: Dict[str, Any], user_id: int,
                       dataset_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a report with user tracking.
        
        Args:
            df: Data to include in report
            report_type: Type of report (html, excel, markdown)
            params: Report parameters (title, sections, etc.)
            user_id: User generating the report
            dataset_id: Optional source dataset ID
            
        Returns:
            Dictionary with report content and metadata
        """
        try:
            title = params.get('title', 'Data Analysis Report')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            result = {
                'report_type': report_type,
                'title': title,
                'generated_at': timestamp,
                'user_id': user_id,
                'dataset_id': dataset_id,
                'params': params
            }
            
            if report_type == 'html':
                html_content = self.generator.generate_html_report(
                    df=df,
                    title=title,
                    include_eda=params.get('include_eda', True),
                    include_visualizations=params.get('include_visualizations', True),
                    include_modeling=params.get('include_modeling', False)
                )
                result['content'] = html_content
                result['format'] = 'text/html'
                result['extension'] = '.html'
                
            elif report_type == 'excel':
                excel_bytes = self._generate_excel_report(df, title, params)
                result['content'] = excel_bytes
                result['format'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                result['extension'] = '.xlsx'
                
            elif report_type == 'markdown':
                md_content = self._generate_markdown_report(df, title, params)
                result['content'] = md_content
                result['format'] = 'text/markdown'
                result['extension'] = '.md'
                
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
            
            logger.info(f"User {user_id} generated {report_type} report: {title}")
            
            return result
            
        except Exception as e:
            logger.error(f"Report generation failed for user {user_id}: {e}")
            raise
    
    def _generate_excel_report(self, df: pd.DataFrame, title: str,
                              params: Dict) -> bytes:
        """Generate Excel report with multiple sheets."""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Rows', 'Columns', 'Memory Usage (KB)', 'Generated At'],
                'Value': [
                    df.shape[0],
                    df.shape[1],
                    df.memory_usage(deep=True).sum() / 1024,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Data sheet
            df.to_excel(writer, sheet_name='Data', index=False)
            
            # Statistics sheet
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                desc = numeric_df.describe().T
                desc.to_excel(writer, sheet_name='Statistics')
        
        return output.getvalue()
    
    def _generate_markdown_report(self, df: pd.DataFrame, title: str,
                                 params: Dict) -> str:
        """Generate Markdown report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        md = f"# {title}\n\n"
        md += f"**Generated:** {timestamp}\n\n"
        md += f"**Rows:** {df.shape[0]:,}\n\n"
        md += f"**Columns:** {df.shape[1]}\n\n"
        md += f"**Memory Usage:** {df.memory_usage(deep=True).sum() / 1024:.2f} KB\n\n"
        
        md += "## Column Overview\n\n"
        md += "| Column | Type | Missing Values |\n"
        md += "|--------|------|----------------|\n"
        
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_pct = (missing_count / len(df)) * 100
            md += f"| {col} | {df[col].dtype} | {missing_count} ({missing_pct:.1f}%) |\n"
        
        md += "\n## Summary Statistics\n\n"
        
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            desc = numeric_df.describe()
            md += desc.to_markdown()
        
        return md
    
    def get_user_reports(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's report history."""
        # This would query the database in production
        # For now, return empty list
        return []


# Singleton instance
report_service = ReportService()
