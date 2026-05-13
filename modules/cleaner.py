"""
Data Cleaning Engine - Smart data cleaning and preprocessing
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder
import streamlit as st

class DataCleaner:
    """Intelligent data cleaning with recommendations."""

    CLEANING_METHODS = {
        "missing": ["drop", "mean", "median", "mode", "constant", "knn", "forward_fill", "backward_fill"],
        "outliers": ["clip_iqr", "clip_zscore", "remove", "log_transform", "none"],
        "duplicates": ["drop_all", "keep_first", "keep_last", "none"],
        "scaling": ["standard", "minmax", "robust", "none"],
        "encoding": ["label", "onehot", "ordinal", "none"]
    }

    @staticmethod
    def get_recommendations(df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Get smart cleaning recommendations."""
        recommendations = {
            "missing": [],
            "outliers": [],
            "duplicates": [],
            "type_conversions": []
        }

        # Missing values recommendations
        for col in df.columns:
            missing_pct = df[col].isnull().mean() * 100
            if missing_pct > 0:
                if missing_pct > 50:
                    rec = {"column": col, "issue": f"{missing_pct:.1f}% missing", "action": "drop_column", "priority": "high"}
                elif pd.api.types.is_numeric_dtype(df[col]):
                    rec = {"column": col, "issue": f"{missing_pct:.1f}% missing", "action": "median_impute", "priority": "medium"}
                else:
                    rec = {"column": col, "issue": f"{missing_pct:.1f}% missing", "action": "mode_impute", "priority": "medium"}
                recommendations["missing"].append(rec)

        # Outlier recommendations
        for col in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
            if outlier_count > len(df) * 0.05:
                recommendations["outliers"].append({
                    "column": col,
                    "issue": f"{outlier_count} outliers ({outlier_count/len(df)*100:.1f}%)",
                    "action": "clip_iqr",
                    "priority": "medium"
                })

        # Duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            recommendations["duplicates"].append({
                "issue": f"{dup_count} duplicate rows",
                "action": "drop_duplicates",
                "priority": "high" if dup_count > len(df) * 0.1 else "low"
            })

        return recommendations

    @staticmethod
    def handle_missing(df: pd.DataFrame, strategy: str = "median", 
                       columns: Optional[List[str]] = None,
                       fill_value: Any = None) -> Tuple[pd.DataFrame, Dict]:
        """Handle missing values with specified strategy."""
        df = df.copy()
        log = {"strategy": strategy, "columns_affected": [], "rows_dropped": 0}

        if columns is None:
            columns = df.columns[df.isnull().any()].tolist()

        if strategy == "drop":
            before = len(df)
            df = df.dropna(subset=columns)
            log["rows_dropped"] = before - len(df)
            log["columns_affected"] = columns
        elif strategy == "mean":
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col].fillna(df[col].mean(), inplace=True)
                    log["columns_affected"].append(col)
        elif strategy == "median":
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col].fillna(df[col].median(), inplace=True)
                    log["columns_affected"].append(col)
        elif strategy == "mode":
            for col in columns:
                df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "Unknown", inplace=True)
                log["columns_affected"].append(col)
        elif strategy == "constant":
            for col in columns:
                val = fill_value if fill_value is not None else "MISSING"
                df[col].fillna(val, inplace=True)
                log["columns_affected"].append(col)
        elif strategy == "knn":
            numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
            if numeric_cols:
                imputer = KNNImputer(n_neighbors=5)
                df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
                log["columns_affected"] = numeric_cols
        elif strategy == "forward_fill":
            df[columns] = df[columns].fillna(method='ffill')
            log["columns_affected"] = columns
        elif strategy == "backward_fill":
            df[columns] = df[columns].fillna(method='bfill')
            log["columns_affected"] = columns

        return df, log

    @staticmethod
    def handle_outliers(df: pd.DataFrame, method: str = "clip_iqr",
                        columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict]:
        """Handle outliers using specified method."""
        df = df.copy()
        log = {"method": method, "columns_affected": [], "outliers_treated": 0}

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            before_count = len(df)

            if method == "clip_iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                df[col] = df[col].clip(lower, upper)
                log["outliers_treated"] += before_count - len(df[df[col].between(lower, upper)])

            elif method == "clip_zscore":
                mean = df[col].mean()
                std = df[col].std()
                lower = mean - 3 * std
                upper = mean + 3 * std
                df[col] = df[col].clip(lower, upper)

            elif method == "remove":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                df = df[df[col].between(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)]
                log["outliers_treated"] += before_count - len(df)

            elif method == "log_transform":
                if df[col].min() >= 0:
                    df[col] = np.log1p(df[col])

            log["columns_affected"].append(col)

        return df, log

    @staticmethod
    def handle_duplicates(df: pd.DataFrame, strategy: str = "drop_all") -> Tuple[pd.DataFrame, Dict]:
        """Handle duplicate rows."""
        df = df.copy()
        before = len(df)
        log = {"strategy": strategy, "rows_removed": 0}

        if strategy == "drop_all":
            df = df.drop_duplicates()
        elif strategy == "keep_first":
            df = df.drop_duplicates(keep='first')
        elif strategy == "keep_last":
            df = df.drop_duplicates(keep='last')

        log["rows_removed"] = before - len(df)
        return df, log

    @staticmethod
    def scale_features(df: pd.DataFrame, method: str = "standard",
                       columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict, Any]:
        """Scale numeric features."""
        df = df.copy()
        log = {"method": method, "columns_affected": []}

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        scaler = None
        if method == "standard":
            scaler = StandardScaler()
        elif method == "minmax":
            scaler = MinMaxScaler()
        elif method == "robust":
            scaler = RobustScaler()

        if scaler:
            df[columns] = scaler.fit_transform(df[columns])
            log["columns_affected"] = columns

        return df, log, scaler

    @staticmethod
    def encode_categorical(df: pd.DataFrame, method: str = "label",
                          columns: Optional[List[str]] = None,
                          drop_first: bool = True) -> Tuple[pd.DataFrame, Dict, Any]:
        """Encode categorical features."""
        df = df.copy()
        log = {"method": method, "columns_affected": [], "encoders": {}}

        if columns is None:
            columns = df.select_dtypes(include=['object', 'category']).columns.tolist()

        if method == "label":
            for col in columns:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                log["columns_affected"].append(col)
                log["encoders"][col] = le

        elif method == "onehot":
            df = pd.get_dummies(df, columns=columns, drop_first=drop_first)
            log["columns_affected"] = columns

        return df, log, log["encoders"]

    @staticmethod
    def auto_clean(df: pd.DataFrame, aggressive: bool = False) -> Tuple[pd.DataFrame, List[Dict]]:
        """Automatically clean dataframe with smart defaults."""
        logs = []

        # Drop columns with >70% missing
        high_missing = [c for c in df.columns if df[c].isnull().mean() > 0.7]
        if high_missing:
            df = df.drop(columns=high_missing)
            logs.append({"step": "drop_high_missing", "columns": high_missing, "reason": ">70% missing"})

        # Handle remaining missing
        df, log = DataCleaner.handle_missing(df, strategy="median")
        if log["columns_affected"]:
            logs.append({"step": "impute_missing", **log})

        # Drop duplicates
        df, log = DataCleaner.handle_duplicates(df, strategy="drop_all")
        if log["rows_removed"] > 0:
            logs.append({"step": "drop_duplicates", **log})

        if aggressive:
            # Clip outliers
            df, log = DataCleaner.handle_outliers(df, method="clip_iqr")
            if log["columns_affected"]:
                logs.append({"step": "clip_outliers", **log})

        return df, logs
