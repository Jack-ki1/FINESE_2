"""
EDA Engine - Automated Exploratory Data Analysis
Leverages ydata-profiling, sweetviz, and custom analysis
"""
import io
import tempfile
import os
import base64
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import traceback

class EDAEngine:
    """Comprehensive EDA engine with multiple analysis modes."""

    @staticmethod
    def quick_profile(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a quick statistical profile."""
        try:
            profile = {
                "shape": df.shape,
                "dtypes": df.dtypes.to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "missing": {
                    col: {"count": int(df[col].isnull().sum()), "pct": float(df[col].isnull().mean() * 100)}
                    for col in df.columns
                },
                "numeric_summary": {},
                "categorical_summary": {},
                "correlations": {}
            }

            # Numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                try:
                    profile["numeric_summary"][col] = {
                        "mean": float(df[col].mean()) if not df[col].empty else 0,
                        "median": float(df[col].median()) if not df[col].empty else 0,
                        "std": float(df[col].std()) if not df[col].empty else 0,
                        "min": float(df[col].min()) if not df[col].empty else 0,
                        "max": float(df[col].max()) if not df[col].empty else 0,
                        "skewness": float(df[col].skew()) if not df[col].empty else 0,
                        "kurtosis": float(df[col].kurtosis()) if not df[col].empty else 0,
                        "q1": float(df[col].quantile(0.25)) if not df[col].empty else 0,
                        "q3": float(df[col].quantile(0.75)) if not df[col].empty else 0,
                        "iqr": float(df[col].quantile(0.75) - df[col].quantile(0.25)) if not df[col].empty else 0
                    }
                except Exception as e:
                    st.warning(f"Could not compute statistics for numeric column '{col}': {str(e)}")

            # Categorical columns
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            for col in cat_cols:
                try:
                    profile["categorical_summary"][col] = {
                        "unique": int(df[col].nunique()),
                        "top_values": df[col].value_counts().head(5).to_dict(),
                        "top_pct": (df[col].value_counts().head(1).iloc[0] / len(df) * 100) if len(df) > 0 else 0
                    }
                except Exception as e:
                    st.warning(f"Could not compute statistics for categorical column '{col}': {str(e)}")

            # Correlations for numeric columns
            if len(numeric_cols) > 1:
                try:
                    corr_matrix = df[numeric_cols].corr()
                    profile["correlations"] = {
                        "strong_positive": [],
                        "strong_negative": [],
                        "high_pairs": []
                    }
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            corr_val = corr_matrix.iloc[i, j]
                            if pd.notna(corr_val) and abs(corr_val) > 0.7:
                                pair = {
                                    "col1": corr_matrix.columns[i],
                                    "col2": corr_matrix.columns[j],
                                    "correlation": float(corr_val)
                                }
                                profile["correlations"]["high_pairs"].append(pair)
                                if corr_val > 0.7:
                                    profile["correlations"]["strong_positive"].append(pair)
                                else:
                                    profile["correlations"]["strong_negative"].append(pair)
                except Exception as e:
                    st.warning(f"Could not compute correlations: {str(e)}")

            return profile
        except Exception as e:
            st.error(f"Error in quick_profile: {str(e)}")
            traceback.print_exc()
            return {}

    @staticmethod
    def detect_issues(df: pd.DataFrame) -> Dict[str, Any]:
        """Detect data quality issues."""
        try:
            issues = {
                "missing_high": [],
                "missing_medium": [],
                "constant_columns": [],
                "high_cardinality": [],
                "duplicates": int(df.duplicated().sum()),
                "outliers": {},
                "skewed": []
            }

            for col in df.columns:
                try:
                    missing_pct = df[col].isnull().mean() * 100
                    if missing_pct > 50:
                        issues["missing_high"].append({"column": col, "pct": missing_pct})
                    elif missing_pct > 10:
                        issues["missing_medium"].append({"column": col, "pct": missing_pct})

                    if df[col].nunique() == 1:
                        issues["constant_columns"].append(col)

                    if df[col].dtype == 'object' and df[col].nunique() / len(df) > 0.9:
                        issues["high_cardinality"].append({"column": col, "unique": df[col].nunique()})

                    if pd.api.types.is_numeric_dtype(df[col]):
                        skew = df[col].skew()
                        if pd.notna(skew) and abs(skew) > 2:
                            issues["skewed"].append({"column": col, "skewness": skew})

                        # IQR outliers
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        outlier_count = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
                        if outlier_count > 0:
                            issues["outliers"][col] = int(outlier_count)
                except Exception as e:
                    st.warning(f"Could not analyze column '{col}': {str(e)}")

            return issues
        except Exception as e:
            st.error(f"Error in detect_issues: {str(e)}")
            traceback.print_exc()
            return {}

    @staticmethod
    def generate_ydata_report(df: pd.DataFrame) -> Optional[str]:
        """Generate ydata-profiling HTML report."""
        try:
            from ydata_profiling import ProfileReport
            profile = ProfileReport(df, title="Data Profiling Report", explorative=True)
            return profile.to_html()
        except ImportError:
            try:
                from data_profiling import ProfileReport
                profile = ProfileReport(df, title="Data Profiling Report", explorative=True)
                return profile.to_html()
            except ImportError:
                return None
        except Exception as e:
            st.error(f"Error generating ydata report: {str(e)}")
            return None

    @staticmethod
    def generate_sweetviz_report(df: pd.DataFrame, target_col: Optional[str] = None) -> Optional[str]:
        """Generate Sweetviz HTML report."""
        try:
            import sweetviz as sv
            if target_col and target_col in df.columns:
                report = sv.analyze([df, "Data"], target_feat=target_col)
            else:
                report = sv.analyze([df, "Data"])

            # Create a unique temporary file path
            temp_file_path = tempfile.mktemp(suffix='.html')
            
            # Generate the report to the temporary file
            report.show_html(filepath=temp_file_path, open_browser=False)
            
            # Read the content of the file
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up by removing the temporary file
            os.unlink(temp_file_path)
            
            return content
        except Exception as e:
            st.error(f"Error generating Sweetviz report: {str(e)}")
            return None

    @staticmethod
    def create_distribution_plot(df: pd.DataFrame, col: str) -> go.Figure:
        """Create distribution plot for a column."""
        try:
            if pd.api.types.is_numeric_dtype(df[col]):
                fig = make_subplots(rows=2, cols=1, 
                                   subplot_titles=(f"Histogram of {col}", f"Box Plot of {col}"),
                                   row_heights=[0.7, 0.3])

                fig.add_trace(go.Histogram(x=df[col].dropna(), nbinsx=50, 
                                          marker_color='#00D4AA', name="Distribution"), row=1, col=1)
                fig.add_trace(go.Box(x=df[col].dropna(), marker_color='#6C63FF', name="Box"), row=2, col=1)

                fig.update_layout(showlegend=False, template="plotly_dark", height=500,
                                 paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            else:
                value_counts = df[col].value_counts().head(20)
                fig = go.Figure(data=[go.Bar(
                    x=value_counts.index,
                    y=value_counts.values,
                    marker_color='#00D4AA'
                )])
                fig.update_layout(title=f"Value Counts: {col}", template="plotly_dark",
                                 paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

            return fig
        except Exception as e:
            st.error(f"Error creating distribution plot for {col}: {str(e)}")
            # Return an empty figure as fallback
            return go.Figure().update_layout(title="Error generating plot")

    @staticmethod
    def create_correlation_heatmap(df: pd.DataFrame) -> Optional[go.Figure]:
        """Create correlation heatmap."""
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            if numeric_df.empty or len(numeric_df.columns) < 2:
                return None

            corr = numeric_df.corr()

            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.columns,
                colorscale=[[0, '#E74C3C'], [0.5, '#2C3E50'], [1, '#00D4AA']],
                zmid=0,
                text=np.round(corr.values, 2),
                texttemplate="%{text}",
                textfont={"size": 10}
            ))

            fig.update_layout(title="Correlation Matrix", template="plotly_dark",
                             height=600, width=700,
                             paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig
        except Exception as e:
            st.error(f"Error creating correlation heatmap: {str(e)}")
            return None

    @staticmethod
    def create_pairplot(df: pd.DataFrame, cols: list, color_col: Optional[str] = None) -> Optional[go.Figure]:
        """Create pairplot using plotly."""
        try:
            if len(cols) > 5:
                cols = cols[:5]  # Limit to prevent performance issues

            fig = px.scatter_matrix(df, dimensions=cols, color=color_col,
                                   template="plotly_dark",
                                   title="Pairwise Relationships")
            fig.update_traces(diagonal_visible=False)
            fig.update_layout(height=800, width=900,
                             paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig
        except Exception as e:
            st.error(f"Error creating pairplot: {str(e)}")
            return None

    @staticmethod
    def create_missing_heatmap(df: pd.DataFrame) -> Optional[go.Figure]:
        """Create missing values heatmap."""
        try:
            missing = df.isnull().astype(int)

            fig = go.Figure(data=go.Heatmap(
                z=missing.values.T,
                x=list(range(len(missing))),
                y=missing.columns,
                colorscale=[[0, '#1C1F26'], [1, '#E74C3C']],
                showscale=False
            ))

            fig.update_layout(title="Missing Values Pattern", template="plotly_dark",
                             height=max(400, len(df.columns) * 30),
                             paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig
        except Exception as e:
            st.error(f"Error creating missing values heatmap: {str(e)}")
            return None