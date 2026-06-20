"""
Statistical Analysis Engine - Hypothesis testing, correlations, regressions
Refactored: No Streamlit dependencies
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, ttest_rel, f_oneway, shapiro, normaltest
from scipy.stats import pearsonr, spearmanr, kendalltau
import statsmodels.api as sm


class StatisticalAnalyzer:
    """Comprehensive statistical analysis suite."""

    @staticmethod
    def _sample_dataframe(df: pd.DataFrame, max_rows: int = 10000) -> pd.DataFrame:
        """Sample dataframe if it exceeds max_rows."""
        if len(df) <= max_rows:
            return df
        frac = max_rows / len(df)
        return df.sample(frac=frac, random_state=42)

    @staticmethod
    def summary_statistics(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Enhanced descriptive statistics."""
        df = StatisticalAnalyzer._sample_dataframe(df)
        if columns:
            df = df[columns]

        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {}

        desc = numeric_df.describe().T
        desc['missing'] = numeric_df.isnull().sum()
        desc['missing_pct'] = numeric_df.isnull().mean() * 100
        desc['skewness'] = numeric_df.skew()
        desc['kurtosis'] = numeric_df.kurtosis()
        desc['variance'] = numeric_df.var()
        desc['range'] = numeric_df.max() - numeric_df.min()

        return desc.round(4).to_dict(orient='index')

    @staticmethod
    def hypothesis_test(df: pd.DataFrame, test_type: str, column1: str,
                       column2: Optional[str] = None,
                       group_column: Optional[str] = None) -> Dict[str, Any]:
        """Perform hypothesis testing."""
        df = StatisticalAnalyzer._sample_dataframe(df)

        if test_type == "t_test":
            if group_column:
                groups = df[group_column].dropna().unique()
                if len(groups) != 2:
                    return {"error": "T-test requires exactly 2 groups"}
                group1 = df[df[group_column] == groups[0]][column1].dropna()
                group2 = df[df[group_column] == groups[1]][column1].dropna()
                stat, p_value = ttest_ind(group1, group2, equal_var=False)
                return {
                    "test": "Independent t-test (Welch's)",
                    "statistic": float(stat), "p_value": float(p_value),
                    "significant": p_value < 0.05,
                    "group1_mean": float(group1.mean()), "group2_mean": float(group2.mean()),
                    "interpretation": "Significant difference" if p_value < 0.05 else "No significant difference"
                }
        elif test_type == "anova":
            if group_column:
                groups = []
                for group in df[group_column].dropna().unique():
                    groups.append(df[df[group_column] == group][column1].dropna())
                stat, p_value = f_oneway(*groups)
                return {
                    "test": "One-way ANOVA",
                    "statistic": float(stat), "p_value": float(p_value),
                    "significant": p_value < 0.05,
                    "interpretation": "Significant difference" if p_value < 0.05 else "No significant difference"
                }
        elif test_type == "chi_square":
            if column2:
                contingency = pd.crosstab(df[column1], df[column2])
                chi2, p_value, dof, expected = chi2_contingency(contingency)
                return {
                    "test": "Chi-square test",
                    "chi2": float(chi2), "p_value": float(p_value), "dof": int(dof),
                    "significant": p_value < 0.05,
                    "interpretation": "Variables are dependent" if p_value < 0.05 else "Variables are independent"
                }

        return {"error": "Invalid test configuration"}

    @staticmethod
    def correlation_analysis(df: pd.DataFrame, columns: List[str],
                            method: str = "pearson") -> Dict[str, Any]:
        """Comprehensive correlation analysis."""
        df = StatisticalAnalyzer._sample_dataframe(df)
        numeric_df = df[columns].select_dtypes(include=[np.number])

        if numeric_df.empty or len(numeric_df.columns) < 2:
            return {"error": "Need at least 2 numeric columns"}

        corr_matrix = numeric_df.corr(method=method)

        significant = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]
                mask = numeric_df[[col1, col2]].notna().all(axis=1)
                if method == "pearson":
                    _, p_val = pearsonr(numeric_df.loc[mask, col1], numeric_df.loc[mask, col2])
                elif method == "spearman":
                    _, p_val = spearmanr(numeric_df.loc[mask, col1], numeric_df.loc[mask, col2])
                else:
                    _, p_val = kendalltau(numeric_df.loc[mask, col1], numeric_df.loc[mask, col2])

                if abs(corr_val) > 0.5 and p_val < 0.05:
                    significant.append({
                        "column1": col1, "column2": col2,
                        "correlation": float(corr_val), "p_value": float(p_val),
                        "strength": "Strong" if abs(corr_val) > 0.7 else "Moderate",
                        "direction": "Positive" if corr_val > 0 else "Negative"
                    })

        return {
            "matrix": corr_matrix.to_dict(),
            "significant_pairs": significant,
            "method": method
        }

    @staticmethod
    def regression_analysis(df: pd.DataFrame, dependent: str,
                           independent: List[str]) -> Dict[str, Any]:
        """Perform multiple linear regression."""
        df = StatisticalAnalyzer._sample_dataframe(df)
        data = df[independent + [dependent]].dropna()

        X = data[independent]
        X = sm.add_constant(X)
        y = data[dependent]

        model = sm.OLS(y, X).fit()

        return {
            "r_squared": float(model.rsquared),
            "adj_r_squared": float(model.rsquared_adj),
            "f_statistic": float(model.fvalue),
            "f_pvalue": float(model.f_pvalue),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "coefficients": {str(k): float(v) for k, v in model.params.to_dict().items()},
            "p_values": {str(k): float(v) for k, v in model.pvalues.to_dict().items()},
            "summary": str(model.summary())
        }

    @staticmethod
    def anova_test(df: pd.DataFrame, group_column: str,
                  value_column: str) -> Dict[str, Any]:
        """Perform one-way ANOVA test."""
        df = StatisticalAnalyzer._sample_dataframe(df)
        groups = []
        group_names = df[group_column].dropna().unique()

        for group in group_names:
            groups.append(df[df[group_column] == group][value_column].dropna())

        stat, p_value = f_oneway(*groups)

        return {
            "test": "One-way ANOVA",
            "statistic": float(stat), "p_value": float(p_value),
            "significant": p_value < 0.05, "groups": len(group_names),
            "interpretation": "Significant difference" if p_value < 0.05 else "No significant difference"
        }

    @staticmethod
    def normality_test(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Test if data follows normal distribution."""
        df = StatisticalAnalyzer._sample_dataframe(df)
        data = df[column].dropna()

        if len(data) > 5000:
            stat, p_value = normaltest(data)
            test_name = "D'Agostino-Pearson"
        else:
            stat, p_value = shapiro(data)
            test_name = "Shapiro-Wilk"

        return {
            "test": test_name, "statistic": float(stat), "p_value": float(p_value),
            "is_normal": p_value > 0.05,
            "interpretation": "Normal distribution" if p_value > 0.05 else "Not normal distribution"
        }
