"""
EDA Engine - Automated Exploratory Data Analysis
Refactored: No Streamlit dependencies
"""
import io
import tempfile
import os
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
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
                "dtypes": {k: str(v) for k, v in df.dtypes.to_dict().items()},
                "memory_usage": int(df.memory_usage(deep=True).sum()),
                "missing": {
                    col: {"count": int(df[col].isnull().sum()), "pct": float(df[col].isnull().mean() * 100)}
                    for col in df.columns
                },
                "numeric_summary": {},
                "categorical_summary": {},
                "correlations": {}
            }

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
                except Exception:
                    pass

            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            for col in cat_cols:
                try:
                    vc = df[col].value_counts().head(5)
                    profile["categorical_summary"][col] = {
                        "unique": int(df[col].nunique()),
                        "top_values": {str(k): int(v) for k, v in vc.to_dict().items()},
                        "top_pct": float((vc.iloc[0] / len(df) * 100)) if len(df) > 0 and len(vc) > 0 else 0
                    }
                except Exception:
                    pass

            if len(numeric_cols) > 1:
                try:
                    corr_matrix = df[numeric_cols].corr()
                    profile["correlations"] = {"strong_positive": [], "strong_negative": [], "high_pairs": []}
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            corr_val = corr_matrix.iloc[i, j]
                            if pd.notna(corr_val) and abs(corr_val) > 0.7:
                                pair = {"col1": corr_matrix.columns[i], "col2": corr_matrix.columns[j], "correlation": float(corr_val)}
                                profile["correlations"]["high_pairs"].append(pair)
                                if corr_val > 0.7:
                                    profile["correlations"]["strong_positive"].append(pair)
                                else:
                                    profile["correlations"]["strong_negative"].append(pair)
                except Exception:
                    pass

            return profile
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    def detect_issues(df: pd.DataFrame) -> Dict[str, Any]:
        """Detect data quality issues."""
        try:
            issues = {
                "missing_high": [], "missing_medium": [],
                "constant_columns": [], "high_cardinality": [],
                "duplicates": int(df.duplicated().sum()),
                "outliers": {}, "skewed": []
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
                            issues["skewed"].append({"column": col, "skewness": float(skew)})

                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        outlier_count = int(((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum())
                        if outlier_count > 0:
                            issues["outliers"][col] = outlier_count
                except Exception:
                    pass

            return issues
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    def generate_ydata_report(df: pd.DataFrame) -> Optional[str]:
        """Generate ydata-profiling HTML report."""
        try:
            from ydata_profiling import ProfileReport
            profile = ProfileReport(df, title="Data Profiling Report", explorative=True)
            return profile.to_html()
        except ImportError:
            return None
        except Exception:
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
                    x=value_counts.index, y=value_counts.values,
                    marker_color='#00D4AA'
                )])
                fig.update_layout(title=f"Value Counts: {col}", template="plotly_dark",
                                 paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig
        except Exception:
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
                z=corr.values, x=corr.columns, y=corr.columns,
                colorscale=[[0, '#E74C3C'], [0.5, '#2C3E50'], [1, '#00D4AA']],
                zmid=0, text=np.round(corr.values, 2),
                texttemplate="%{text}", textfont={"size": 10}
            ))
            fig.update_layout(title="Correlation Matrix", template="plotly_dark",
                             height=600, width=700,
                             paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig
        except Exception:
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
        except Exception:
            return go.Figure().update_layout(title="Error generating plot")
