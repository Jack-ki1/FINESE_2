"""
Data Dictionary Component for FINESE2
Provides detailed information about dataset columns
"""
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import plotly.express as px


class DataDictionary:
    """Manages and displays information about dataset columns."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.columns_info = self._analyze_columns()
    
    def _analyze_columns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all columns in the DataFrame."""
        info = {}
        
        for col in self.df.columns:
            col_data = self.df[col]
            col_info = {
                'name': col,
                'dtype': str(col_data.dtype),
                'non_null_count': col_data.count(),
                'null_count': col_data.isnull().sum(),
                'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
                'unique_count': col_data.nunique(),
                'unique_percentage': (col_data.nunique() / len(col_data)) * 100,
            }
            
            # Additional stats based on data type
            if pd.api.types.is_numeric_dtype(col_data) and not pd.api.types.is_bool_dtype(col_data):
                col_info.update({
                    'type_category': 'numeric',
                    'min': col_data.min(),
                    'max': col_data.max(),
                    'mean': col_data.mean(),
                    'std': col_data.std(),
                    'median': col_data.median(),
                    'q25': col_data.quantile(0.25),
                    'q75': col_data.quantile(0.75),
                })
            elif pd.api.types.is_bool_dtype(col_data):
                # Handle boolean columns specially
                col_info.update({
                    'type_category': 'boolean',
                    'min': None,  # Booleans don't have min/max in numeric sense
                    'max': None,
                    'mean': col_data.mean(),
                    'std': col_data.std(),
                    'median': None,
                    'q25': None,
                    'q75': None,
                })
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                col_info.update({
                    'type_category': 'datetime',
                    'min_date': col_data.min(),
                    'max_date': col_data.max(),
                    'date_range': (col_data.max() - col_data.min()).days,
                })
            else:
                col_info.update({
                    'type_category': 'categorical',
                    'top_value': col_data.mode().iloc[0] if not col_data.mode().empty else None,
                    'top_value_count': col_data.value_counts().iloc[0] if not col_data.value_counts().empty else 0,
                })
            
            # Determine quality score
            quality_score = self._calculate_quality_score(col_data)
            col_info['quality_score'] = quality_score
            
            info[col] = col_info
        
        return info
    
    def _calculate_quality_score(self, series: pd.Series) -> float:
        """Calculate a quality score for a column (0-100)."""
        score = 100
        
        # Deduct points for null values
        null_ratio = series.isnull().sum() / len(series)
        score -= null_ratio * 50  # Up to 50 points deducted for nulls
        
        # For numeric data, check for infinite values
        if pd.api.types.is_numeric_dtype(series):
            inf_count = np.isinf(series).sum()
            inf_ratio = inf_count / len(series)
            score -= inf_ratio * 30  # Up to 30 points deducted for infinite values
        
        # For categorical data, check for excessive cardinality
        if not pd.api.types.is_numeric_dtype(series):
            unique_ratio = series.nunique() / len(series)
            if unique_ratio > 0.9:  # Too many unique values might indicate poor quality
                score -= 20
        
        return max(0, min(100, score))
    
    def get_summary_df(self) -> pd.DataFrame:
        """Get a summary DataFrame of all columns."""
        data = []
        for col_name, info in self.columns_info.items():
            data.append({
                'Column': col_name,
                'Type': info['dtype'],
                'Category': info['type_category'],
                'Non-Null Count': info['non_null_count'],
                'Null Count': info['null_count'],
                'Null %': round(info['null_percentage'], 2),
                'Unique Count': info['unique_count'],
                'Quality Score': round(info['quality_score'], 1),
            })
        
        return pd.DataFrame(data)
    
    def get_column_details(self, col_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific column."""
        return self.columns_info.get(col_name, {})
    
    def render_interactive_dictionary(self):
        """Render an interactive data dictionary component."""
        st.subheader("📚 Interactive Data Dictionary")
        
        # Summary table
        summary_df = self.get_summary_df()
        
        # Add color coding based on quality score
        def color_quality(val):
            if val >= 80:
                color = 'green'
            elif val >= 50:
                color = 'orange'
            else:
                color = 'red'
            return f'color: {color}; font-weight: bold'
        
        styled_df = summary_df.style.format({
            'Quality Score': lambda x: f"{x}%",
            'Null %': lambda x: f"{x}%"
        }).applymap(color_quality, subset=['Quality Score'])
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Detailed view for selected column
        st.subheader("🔍 Column Details")
        selected_col = st.selectbox("Select a column for details", self.df.columns.tolist())
        
        if selected_col:
            col_info = self.get_column_details(selected_col)
            self._display_column_details(selected_col, col_info)
    
    def _display_column_details(self, col_name: str, col_info: Dict[str, Any]):
        """Display detailed information for a specific column."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Data Type", col_info['dtype'])
            st.metric("Quality Score", f"{col_info['quality_score']:.1f}/100")
            st.metric("Non-Null Count", col_info['non_null_count'])
        
        with col2:
            st.metric("Null Count", col_info['null_count'])
            st.metric("Null Percentage", f"{col_info['null_percentage']:.2f}%")
            st.metric("Unique Values", col_info['unique_count'])
        
        with col3:
            st.metric("Unique Percentage", f"{col_info['unique_percentage']:.2f}%")
            if col_info['type_category'] == 'numeric':
                st.metric("Min Value", col_info['min'])
                st.metric("Max Value", col_info['max'])
            elif col_info['type_category'] == 'categorical':
                top_val = col_info.get('top_value', 'N/A')
                st.metric("Top Value", str(top_val)[:20] + "..." if len(str(top_val)) > 20 else str(top_val))
        
        # Distribution visualization
        if col_info['type_category'] == 'numeric':
            # Histogram for numeric columns
            fig = px.histogram(
                self.df, 
                x=col_name, 
                title=f"Distribution of {col_name}",
                marginal="box"  # Adds a box plot
            )
            st.plotly_chart(fig, use_container_width=True)
        elif col_info['type_category'] == 'categorical':
            # Bar chart for categorical columns
            top_categories = self.df[col_name].value_counts().head(10)
            fig = px.bar(
                x=top_categories.index.astype(str), 
                y=top_categories.values,
                title=f"Top 10 Categories in {col_name}",
                labels={'x': col_name, 'y': 'Count'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Add annotation capability
        st.subheader(f"📝 Annotate {col_name}")
        current_annotation = st.session_state.get(f'annotation_{col_name}', '')
        new_annotation = st.text_area(
            "Add notes about this column", 
            value=current_annotation,
            key=f'annotate_{col_name}',
            help="Add descriptions, observations, or notes about this column"
        )
        
        if st.button(f"Save Annotation for {col_name}", key=f'save_annot_{col_name}'):
            st.session_state[f'annotation_{col_name}'] = new_annotation
            st.success(f"Annotation saved for {col_name}")
        
        if current_annotation:
            st.info(f"**Saved Annotation:** {current_annotation}")


def render_data_dictionary(df: pd.DataFrame):
    """Convenience function to render the data dictionary."""
    if df is not None and not df.empty:
        dd = DataDictionary(df)
        dd.render_interactive_dictionary()
    else:
        st.warning("No data available to analyze")