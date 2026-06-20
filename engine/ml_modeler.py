"""
ML Modeler - Automated Machine Learning
Refactored: No Streamlit dependencies
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

from sklearn.experimental import enable_iterative_imputer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import (
    LinearRegression, Ridge, Lasso, ElasticNet, LogisticRegression, SGDClassifier, SGDRegressor
)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    BaggingClassifier, BaggingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    IsolationForest
)
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, mean_squared_error, mean_absolute_error,
    r2_score, silhouette_score
)
import joblib
import io
import json


class MLModeler:
    CLASSIFICATION_MODELS = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
        "SVM": SVC(probability=True, random_state=42),
        "K-Nearest Neighbors": KNeighborsClassifier(n_jobs=-1),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Naive Bayes": GaussianNB(),
        "AdaBoost": AdaBoostClassifier(random_state=42),
        "Extra Trees": ExtraTreesClassifier(n_estimators=100, random_state=42),
        "Bagging Classifier": BaggingClassifier(random_state=42),
        "SGD Classifier": SGDClassifier(random_state=42),
    }

    REGRESSION_MODELS = {
        "Linear Regression": LinearRegression(),
        "Ridge": Ridge(random_state=42),
        "Lasso": Lasso(random_state=42),
        "ElasticNet": ElasticNet(random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42),
        "SVR": SVR(),
        "K-Nearest Neighbors": KNeighborsRegressor(n_jobs=-1),
        "Decision Tree": DecisionTreeRegressor(random_state=42),
        "AdaBoost": AdaBoostRegressor(random_state=42),
        "Extra Trees": ExtraTreesRegressor(n_estimators=100, random_state=42),
        "Bagging Regressor": BaggingRegressor(random_state=42),
        "SGD Regressor": SGDRegressor(random_state=42),
    }

    @staticmethod
    def prepare_data(df: pd.DataFrame, target_col: str, test_size: float = 0.2,
                     problem_type: Optional[str] = None) -> Tuple:
        df = df.copy()
        df = df.dropna(subset=[target_col])
        X = df.drop(columns=[target_col])
        y = df[target_col]

        if problem_type is None:
            if y.dtype == 'object' or y.dtype.name == 'category' or y.nunique() <= 10:
                problem_type = "classification"
            else:
                problem_type = "regression"

        if problem_type == "classification":
            if y.dtype == 'object' or y.dtype.name == 'category':
                le = LabelEncoder()
                y = pd.Series(le.fit_transform(y.astype(str)), index=y.index, name=y.name)

        X_numeric = X.select_dtypes(include=[np.number])
        X_categorical = X.select_dtypes(include=['object', 'category'])

        X_numeric = X_numeric.fillna(X_numeric.median())

        encoder = None
        if not X_categorical.empty:
            for col in X_categorical.columns:
                mode_val = X_categorical[col].mode()
                fill = mode_val.iloc[0] if not mode_val.empty else 'Unknown'
                X_categorical[col] = X_categorical[col].fillna(fill)

            encoder = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')
            X_categorical_encoded = encoder.fit_transform(X_categorical)
            X_categorical_df = pd.DataFrame(
                X_categorical_encoded,
                columns=encoder.get_feature_names_out(X_categorical.columns),
                index=X_categorical.index
            )
            X_processed = pd.concat([X_numeric, X_categorical_df], axis=1)
        else:
            X_processed = X_numeric

        scaler = StandardScaler()
        X_scaled = pd.DataFrame(
            scaler.fit_transform(X_processed),
            columns=X_processed.columns,
            index=X_processed.index
        )

        stratify = y if problem_type == "classification" else None
        
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=test_size, random_state=42, stratify=stratify
            )
        except ValueError:
            # Fall back to unstratified split if stratification fails (e.g., small classes)
            logger.warning(f"Stratified split failed for {problem_type}, using unstratified split")
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=test_size, random_state=42
            )

        return X_train, X_test, y_train, y_test, problem_type, scaler, encoder

    @staticmethod
    def train_model(X_train, X_test, y_train, y_test, model_name: str, problem_type: str) -> Dict:
        if problem_type == "classification":
            model = MLModeler.CLASSIFICATION_MODELS.get(model_name, RandomForestClassifier(random_state=42))
        else:
            model = MLModeler.REGRESSION_MODELS.get(model_name, RandomForestRegressor(random_state=42))

        if isinstance(model, str) and model.endswith("_not_installed"):
            raise ImportError(f"{model_name} is not installed")

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        if problem_type == "classification":
            metrics = {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision": float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                "recall": float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                "f1": float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
                "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
                "classification_report": classification_report(y_test, y_pred, output_dict=True)
            }
        else:
            metrics = {
                "mse": float(mean_squared_error(y_test, y_pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                "mae": float(mean_absolute_error(y_test, y_pred)),
                "r2": float(r2_score(y_test, y_pred))
            }

        cv_scores = cross_val_score(model, X_train, y_train, cv=5,
                                    scoring='accuracy' if problem_type == "classification" else 'r2')

        importance = None
        if hasattr(model, 'feature_importances_'):
            importance = {str(k): float(v) for k, v in zip(X_train.columns, model.feature_importances_)}
        elif hasattr(model, 'coef_'):
            importance = {str(k): float(v) for k, v in zip(X_train.columns, np.abs(model.coef_).flatten())}

        return {
            "model": model,
            "model_name": model_name,
            "metrics": metrics,
            "cv_scores": cv_scores,
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "feature_importance": importance,
            "predictions": y_pred,
            "actual": y_test.values
        }

    @staticmethod
    def train_models(df: pd.DataFrame, target_col: str, problem_type: Optional[str] = None,
                     models: Optional[List[str]] = None, test_size: float = 0.2) -> Dict:
        """Train multiple models and return results."""
        X_train, X_test, y_train, y_test, inferred_type, scaler, encoder = MLModeler.prepare_data(
            df, target_col, test_size, problem_type
        )
        if problem_type is None:
            problem_type = inferred_type

        available = list(MLModeler.CLASSIFICATION_MODELS.keys()) if problem_type == "classification" else list(MLModeler.REGRESSION_MODELS.keys())
        if models:
            available = [m for m in models if m in available]

        results = {}
        for name in available:
            try:
                result = MLModeler.train_model(X_train, X_test, y_train, y_test, name, problem_type)
                results[name] = result
            except Exception as e:
                logger.warning(f"Failed to train {name}: {str(e)}")

        if not results:
            return {"error": "No models trained successfully"}

        if problem_type == "classification":
            best = max(results.items(), key=lambda x: x[1]["metrics"]["f1"])
        else:
            best = max(results.items(), key=lambda x: x[1]["metrics"]["r2"])

        return {
            "problem_type": problem_type,
            "models": {k: {kk: vv for kk, vv in v.items() if kk != "model"} for k, v in results.items()},
            "best_model": best[0],
            "best_metrics": best[1]["metrics"],
            "feature_columns": X_train.columns.tolist(),
        }

    @staticmethod
    def perform_clustering(df: pd.DataFrame, features: List[str], algorithm: str = "K-Means",
                          n_clusters: int = 3, **kwargs) -> Dict:
        X = df[features].dropna()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        if algorithm == "K-Means":
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        elif algorithm == "DBSCAN":
            model = DBSCAN(eps=kwargs.get("eps", 0.5), min_samples=kwargs.get("min_samples", 5))
        elif algorithm == "Hierarchical":
            model = AgglomerativeClustering(n_clusters=n_clusters)
        elif algorithm == "Gaussian Mixture":
            model = GaussianMixture(n_components=n_clusters, random_state=42)
        else:
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)

        labels = model.fit_predict(X_scaled)

        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        return {
            "labels": labels.tolist(),
            "n_clusters": int(len(np.unique(labels)) if algorithm != "DBSCAN" else len(np.unique(labels[labels >= 0]))),
            "pca_data": X_pca.tolist(),
            "pca_variance": pca.explained_variance_ratio_.tolist(),
            "feature_columns": features,
            "silhouette_score": float(silhouette_score(X_scaled, labels)) if algorithm != "DBSCAN" else None
        }

    @staticmethod
    def predict_with_model(df: pd.DataFrame, model, target_col: str) -> np.ndarray:
        """Make predictions with a trained model."""
        X = df.drop(columns=[target_col], errors='ignore')
        X_numeric = X.select_dtypes(include=[np.number]).fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_numeric)
        return model.predict(X_scaled)

    @staticmethod
    def export_model(model_result: Dict, format: str = "joblib") -> bytes:
        model = model_result["model"]
        buffer = io.BytesIO()
        if format == "joblib":
            joblib.dump(model, buffer)
        elif format == "json":
            info = {
                "model_name": model_result["model_name"],
                "metrics": model_result["metrics"],
                "feature_importance": model_result.get("feature_importance", {}),
                "params": model.get_params() if hasattr(model, 'get_params') else {}
            }
            buffer.write(json.dumps(info, indent=2, default=str).encode())
        buffer.seek(0)
        return buffer.getvalue()
