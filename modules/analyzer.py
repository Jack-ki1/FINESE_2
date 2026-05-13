"""
Statistical Analysis Engine - Hypothesis testing, correlations, regressions
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, ttest_rel, f_oneway, shapiro, normaltest
from scipy.stats import pearsonr, spearmanr, kendalltau
import statsmodels.api as sm
from statsmodels.formula.api import ols
import streamlit as st

class StatisticalAnalyzer:
    """Comprehensive statistical analysis suite."""

    @staticmethod
    def _sample_dataframe(df: pd.DataFrame, max_rows: int = 10000) -> pd.DataFrame:
        """Sample dataframe if it exceeds max_rows."""
        if len(df) <= max_rows:
            return df
        else:
            # Calculate sampling fraction
            frac = max_rows / len(df)
            return df.sample(frac=frac, random_state=42)

    @staticmethod
    def descriptive_stats(df: pd.DataFrame, columns: Optional[List[str]] = None, 
                         sample_if_large: bool = True) -> pd.DataFrame:
        """Enhanced descriptive statistics with optional sampling."""
        if sample_if_large:
            df = StatisticalAnalyzer._sample_dataframe(df)
        
        if columns:
            df = df[columns]

        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return pd.DataFrame()

        desc = numeric_df.describe().T
        desc['missing'] = numeric_df.isnull().sum()
        desc['missing_pct'] = numeric_df.isnull().mean() * 100
        desc['skewness'] = numeric_df.skew()
        desc['kurtosis'] = numeric_df.kurtosis()
        desc['variance'] = numeric_df.var()
        desc['range'] = numeric_df.max() - numeric_df.min()
        desc['iqr'] = numeric_df.quantile(0.75) - numeric_df.quantile(0.25)
        desc['cv'] = (numeric_df.std() / numeric_df.mean()) * 100  # Coefficient of variation

        return desc.round(4)

    @staticmethod
    def normality_test(df: pd.DataFrame, column: str, method: str = "shapiro", 
                      sample_if_large: bool = True) -> Dict[str, Any]:
        """Test if data follows normal distribution with optional sampling."""
        if sample_if_large:
            df = StatisticalAnalyzer._sample_dataframe(df)
            
        data = df[column].dropna()

        if method == "shapiro":
            if len(data) > 5000:
                # Shapiro-Wilk not suitable for large samples, use D'Agostino
                stat, p_value = normaltest(data)
                test_name = "D'Agostino-Pearson"
            else:
                stat, p_value = shapiro(data)
                test_name = "Shapiro-Wilk"
        else:
            stat, p_value = normaltest(data)
            test_name = "D'Agostino-Pearson"

        return {
            "test": test_name,
            "statistic": float(stat),
            "p_value": float(p_value),
            "is_normal": p_value > 0.05,
            "interpretation": "Normal distribution" if p_value > 0.05 else "Not normal distribution"
        }

    @staticmethod
    def correlation_analysis(df: pd.DataFrame, method: str = "pearson", 
                           sample_if_large: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """Comprehensive correlation analysis with optional sampling."""
        if sample_if_large:
            df = StatisticalAnalyzer._sample_dataframe(df)
            
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return pd.DataFrame(), {}

        corr_matrix = numeric_df.corr(method=method)

        # Find significant correlations
        significant = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]

                # Calculate p-value
                mask = numeric_df[[col1, col2]].notna().all(axis=1)
                if method == "pearson":
                    _, p_val = pearsonr(numeric_df.loc[mask, col1], numeric_df.loc[mask, col2])
                elif method == "spearman":
                    _, p_val = spearmanr(numeric_df.loc[mask, col1], numeric_df.loc[mask, col2])
                else:
                    _, p_val = kendalltau(numeric_df.loc[mask, col1], numeric_df.loc[mask, col2])

                if abs(corr_val) > 0.5 and p_val < 0.05:
                    significant.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": float(corr_val),
                        "p_value": float(p_val),
                        "strength": "Strong" if abs(corr_val) > 0.7 else "Moderate",
                        "direction": "Positive" if corr_val > 0 else "Negative"
                    })

        return corr_matrix, {"significant_pairs": significant, "method": method}

    @staticmethod
    def t_test(df: pd.DataFrame, numeric_col: str, categorical_col: str, 
               test_type: str = "independent", sample_if_large: bool = True) -> Dict[str, Any]:
        """Perform t-test with optional sampling."""
        if sample_if_large:
            df = StatisticalAnalyzer._sample_dataframe(df)
            
        groups = df[categorical_col].dropna().unique()

        if len(groups) != 2:
            return {"error": "T-test requires exactly 2 groups"}

        group1 = df[df[categorical_col] == groups[0]][numeric_col].dropna()
        group2 = df[df[categorical_col] == groups[1]][numeric_col].dropna()

        if test_type == "independent":
            stat, p_value = ttest_ind(group1, group2, equal_var=False)
            test_name = "Independent t-test (Welch's)"
        else:
            stat, p_value = ttest_rel(group1, group2)
            test_name = "Paired t-test"

        return {
            "test": test_name,
            "statistic": float(stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "group1_mean": float(group1.mean()),
            "group2_mean": float(group2.mean()),
            "group1_n": len(group1),
            "group2_n": len(group2),
            "interpretation": f"Significant difference between groups" if p_value < 0.05 else "No significant difference"
        }

    @staticmethod
    def anova(df: pd.DataFrame, numeric_col: str, categorical_col: str, 
              sample_if_large: bool = True) -> Dict[str, Any]:
        """Perform one-way ANOVA with optional sampling."""
        if sample_if_large:
            df = StatisticalAnalyzer._sample_dataframe(df)
            
        groups = []
        group_names = df[categorical_col].dropna().unique()

        for group in group_names:
            groups.append(df[df[categorical_col] == group][numeric_col].dropna())

        stat, p_value = f_oneway(*groups)

        return {
            "test": "One-way ANOVA",
            "statistic": float(stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "groups": len(group_names),
            "interpretation": "Significant difference between group means" if p_value < 0.05 else "No significant difference"
        }

    @staticmethod
    def chi_square_test(df: pd.DataFrame, col1: str, col2: str, 
                       sample_if_large: bool = True) -> Dict[str, Any]:
        """Perform chi-square test of independence with optional sampling."""
        if sample_if_large:
            df = StatisticalAnalyzer._sample_dataframe(df)
            
        contingency = pd.crosstab(df[col1], df[col2])
        chi2, p_value, dof, expected = chi2_contingency(contingency)

        return {
            "test": "Chi-square test of independence",
            "chi2": float(chi2),
            "p_value": float(p_value),
            "dof": int(dof),
            "significant": p_value < 0.05,
            "contingency_table": contingency,
            "interpretation": "Variables are dependent" if p_value < 0.05 else "Variables are independent"
        }

    @staticmethod
    def linear_regression(df: pd.DataFrame, target: str, features: List[str], 
                         sample_if_large: bool = True) -> Dict[str, Any]:
        """Perform multiple linear regression with optional sampling."""
        if sample_if_large:
            df = StatisticalAnalyzer._sample_dataframe(df)
            
        data = df[features + [target]].dropna()

        X = data[features]
        X = sm.add_constant(X)
        y = data[target]

        model = sm.OLS(y, X).fit()

        return {
            "r_squared": float(model.rsquared),
            "adj_r_squared": float(model.rsquared_adj),
            "f_statistic": float(model.fvalue),
            "f_pvalue": float(model.f_pvalue),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "coefficients": model.params.to_dict(),
            "p_values": model.pvalues.to_dict(),
            "conf_intervals": model.conf_int().to_dict(),
            "summary": str(model.summary()),
            "residuals": model.resid.values,
            "predicted": model.fittedvalues.values
        }

    @staticmethod
    def run_full_analysis(df: pd.DataFrame, target_col: Optional[str] = None, 
                         sample_if_large: bool = True) -> Dict[str, Any]:
        """Run comprehensive automated analysis with optional sampling."""
        if sample_if_large:
            df = StatisticalAnalyzer._sample_dataframe(df)
            
        results = {
            "descriptive": StatisticalAnalyzer.descriptive_stats(df, sample_if_large=False),  # Already sampled
            "normality": {},
            "correlations": {},
            "insights": []
        }

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        # Normality tests
        for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
            results["normality"][col] = StatisticalAnalyzer.normality_test(df, col, sample_if_large=False)  # Already sampled

        # Correlations
        if len(numeric_cols) >= 2:
            corr_matrix, corr_info = StatisticalAnalyzer.correlation_analysis(df, sample_if_large=False)  # Already sampled
            results["correlations"]["matrix"] = corr_matrix
            results["correlations"]["significant"] = corr_info["significant_pairs"]

        # Auto insights
        for col in numeric_cols:
            skew = df[col].skew()
            if abs(skew) > 2:
                results["insights"].append(f"{col} is highly skewed (skew={skew:.2f})")
            if df[col].isnull().mean() > 0.1:
                results["insights"].append(f"{col} has {df[col].isnull().mean()*100:.1f}% missing values")

        return results