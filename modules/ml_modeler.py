"""
ML Modeler - Automated Machine Learning
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import streamlit as st

# Enable experimental IterativeImputer
from sklearn.experimental import enable_iterative_imputer

from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV,
    StratifiedKFold, KFold, learning_curve, validation_curve
)
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder, OneHotEncoder,
    OrdinalEncoder, PowerTransformer, QuantileTransformer, PolynomialFeatures, FunctionTransformer
)
from sklearn.impute import SimpleImputer, KNNImputer, IterativeImputer
from sklearn.compose import ColumnTransformer
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.feature_selection import (
    SelectKBest, f_classif, mutual_info_regression, mutual_info_classif,
    RFE, RFECV, VarianceThreshold, chi2
)
from sklearn.linear_model import (
    LinearRegression,
    Ridge, 
    Lasso, LassoCV,
    ElasticNet,
    LogisticRegression,
    SGDClassifier,
    SGDRegressor
)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (
    RandomForestClassifier, 
    RandomForestRegressor,
    GradientBoostingClassifier, 
    GradientBoostingRegressor,
    AdaBoostClassifier,
    AdaBoostRegressor,
    BaggingClassifier,
    BaggingRegressor,
    ExtraTreesClassifier, 
    ExtraTreesRegressor,
    IsolationForest,
    VotingClassifier,
    StackingClassifier, 
    StackingRegressor
)
from sklearn.svm import SVC, SVR, LinearSVC, LinearSVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA, TruncatedSVD, NMF
from sklearn.manifold import TSNE
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report, mean_squared_error, mean_absolute_error,
    r2_score, silhouette_score, adjusted_rand_score
)
import joblib
import pickle
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
        "XGBoost": "xgboost_not_installed",
        "LightGBM": "lightgbm_not_installed",
        "CatBoost": "catboost_not_installed"
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
        "XGBoost": "xgboost_not_installed",
        "LightGBM": "lightgbm_not_installed",
        "CatBoost": "catboost_not_installed"
    }
    
    # Initialize advanced models if available
    try:
        from xgboost import XGBClassifier, XGBRegressor
        CLASSIFICATION_MODELS["XGBoost"] = XGBClassifier(random_state=42, verbosity=0)
        REGRESSION_MODELS["XGBoost"] = XGBRegressor(random_state=42, verbosity=0)
    except ImportError:
        pass
    
    try:
        from lightgbm import LGBMClassifier, LGBMRegressor
        CLASSIFICATION_MODELS["LightGBM"] = LGBMClassifier(random_state=42)
        REGRESSION_MODELS["LightGBM"] = LGBMRegressor(random_state=42)
    except ImportError:
        pass
        
    try:
        from catboost import CatBoostClassifier, CatBoostRegressor
        CLASSIFICATION_MODELS["CatBoost"] = CatBoostClassifier(random_state=42, verbose=False)
        REGRESSION_MODELS["CatBoost"] = CatBoostRegressor(random_state=42, verbose=False)
    except ImportError:
        pass

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
        
        # Handle numeric columns
        X_numeric = X_numeric.fillna(X_numeric.median())
        
        # Handle categorical columns
        if not X_categorical.empty:
            # Fill categorical with mode
            for col in X_categorical.columns:
                X_categorical[col] = X_categorical[col].fillna(X_categorical[col].mode().iloc[0] if not X_categorical[col].mode().empty else 'Unknown')
            
            # Encode categorical
            encoder = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')
            X_categorical_encoded = encoder.fit_transform(X_categorical)
            X_categorical_df = pd.DataFrame(
                X_categorical_encoded,
                columns=encoder.get_feature_names_out(X_categorical.columns),
                index=X_categorical.index
            )
            # Combine numeric and categorical
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
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42, stratify=stratify
        )

        return X_train, X_test, y_train, y_test, problem_type, scaler, encoder if 'encoder' in locals() else None

    @staticmethod
    def train_model(X_train, X_test, y_train, y_test, model_name: str, problem_type: str) -> Dict:
        # Get the model based on problem type
        if problem_type == "classification":
            model = MLModeler.CLASSIFICATION_MODELS.get(model_name, RandomForestClassifier(random_state=42))
        else:
            model = MLModeler.REGRESSION_MODELS.get(model_name, RandomForestRegressor(random_state=42))
        
        # Handle special cases for advanced models
        if isinstance(model, str) and model.endswith("_not_installed"):
            raise ImportError(f"{model_name} is not installed. Please install it with pip install {model_name.lower().replace(' ', '')}")
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        if problem_type == "classification":
            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "precision": precision_score(y_test, y_pred, average='weighted', zero_division=0),
                "recall": recall_score(y_test, y_pred, average='weighted', zero_division=0),
                "f1": f1_score(y_test, y_pred, average='weighted', zero_division=0),
                "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
                "classification_report": classification_report(y_test, y_pred, output_dict=True)
            }
        else:
            metrics = {
                "mse": mean_squared_error(y_test, y_pred),
                "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                "mae": mean_absolute_error(y_test, y_pred),
                "r2": r2_score(y_test, y_pred)
            }

        cv_scores = cross_val_score(model, X_train, y_train, cv=5,
                                    scoring='accuracy' if problem_type == "classification" else 'r2')

        importance = None
        if hasattr(model, 'feature_importances_'):
            importance = dict(zip(X_train.columns, model.feature_importances_))
        elif hasattr(model, 'coef_'):
            importance = dict(zip(X_train.columns, np.abs(model.coef_).flatten()))

        return {
            "model": model,
            "model_name": model_name,
            "metrics": metrics,
            "cv_scores": cv_scores,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "feature_importance": importance,
            "predictions": y_pred,
            "actual": y_test.values
        }

    @staticmethod
    def auto_train(df: pd.DataFrame, target_col: str, problem_type: Optional[str] = None,
                   models: Optional[List[str]] = None, test_size: float = 0.2) -> Dict:
        X_train, X_test, y_train, y_test, inferred_type, scaler, encoder = MLModeler.prepare_data(df, target_col, test_size, problem_type)
        if problem_type is None:
            problem_type = inferred_type

        available = list(MLModeler.CLASSIFICATION_MODELS.keys()) if problem_type == "classification" else list(MLModeler.REGRESSION_MODELS.keys())
        if models:
            available = [m for m in models if m in available]

        results = {}
        
        # Create containers for progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        current_model_text = st.empty()
        
        for i, name in enumerate(available):
            current_model_text.text(f"Training {name}...")
            try:
                result = MLModeler.train_model(X_train, X_test, y_train, y_test, name, problem_type)
                results[name] = result
            except ImportError as e:
                st.warning(f"Skipping {name}: {str(e)}")
            except Exception as e:
                st.warning(f"Failed to train {name}: {str(e)}")
            progress_bar.progress((i + 1) / len(available))
            status_text.text(f"Completed {i + 1}/{len(available)} models")
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        current_model_text.empty()

        if problem_type == "classification":
            best = max(results.items(), key=lambda x: x[1]["metrics"]["f1"])
        else:
            best = max(results.items(), key=lambda x: x[1]["metrics"]["r2"])

        return {
            "problem_type": problem_type,
            "models": results,
            "best_model": best[0],
            "best_model_result": best[1],
            "feature_columns": X_train.columns.tolist(),
            "X_train": X_train, "X_test": X_test,
            "y_train": y_train, "y_test": y_test,
            "scaler": scaler,
            "encoder": encoder
        }

    @staticmethod
    def cluster_data(df: pd.DataFrame, features: List[str], algorithm: str = "K-Means",
                     n_clusters: int = 3, **kwargs) -> Dict:
        X = df[features].dropna()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Show progress for clustering
        progress_bar = st.progress(0)
        progress_bar.progress(10)
        status_text = st.empty()
        status_text.text("Scaling features...")
        
        if algorithm == "K-Means":
            status_text.text("Initializing K-Means...")
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        elif algorithm == "DBSCAN":
            status_text.text("Initializing DBSCAN...")
            model = DBSCAN(eps=kwargs.get("eps", 0.5), min_samples=kwargs.get("min_samples", 5))
        elif algorithm == "Hierarchical":
            status_text.text("Initializing Hierarchical...")
            model = AgglomerativeClustering(n_clusters=n_clusters)
        elif algorithm == "Gaussian Mixture":
            status_text.text("Initializing Gaussian Mixture...")
            model = GaussianMixture(n_components=n_clusters, random_state=42)
        else:
            status_text.text("Initializing default clustering...")
            model = KMeans(n_clusters=n_clusters, random_state=42)
        
        progress_bar.progress(50)
        status_text.text(f"Fitting {algorithm} model...")
        
        labels = model.fit_predict(X_scaled)
        
        progress_bar.progress(80)
        status_text.text("Computing PCA for visualization...")
        
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        progress_bar.progress(100)
        status_text.text("Done!")
        # Small delay to show completion
        import time
        time.sleep(0.2)
        progress_bar.empty()
        status_text.empty()

        return {
            "model": model,
            "labels": labels,
            "n_clusters": len(np.unique(labels)) if algorithm != "DBSCAN" else len(np.unique(labels[labels >= 0])),
            "pca_data": X_pca,
            "pca_variance": pca.explained_variance_ratio_.tolist(),
            "feature_columns": features
        }

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

    @staticmethod
    def hyperparameter_tuning(df: pd.DataFrame, target_col: str, model_name: str, 
                              problem_type: Optional[str] = None) -> Dict:
        """
        Perform hyperparameter tuning for a given model using Optuna if available
        """
        try:
            import optuna
            from sklearn.model_selection import cross_val_score
            
            # Prepare data
            X_train, X_test, y_train, y_test, inferred_type, scaler, encoder = MLModeler.prepare_data(
                df, target_col, test_size=0.2, problem_type=problem_type
            )
            
            if problem_type is None:
                problem_type = inferred_type
                
            # Define objective function for optimization
            def objective(trial):
                if model_name == "Random Forest":
                    n_estimators = trial.suggest_int("n_estimators", 10, 200)
                    max_depth = trial.suggest_int("max_depth", 1, 20)
                    min_samples_split = trial.suggest_int("min_samples_split", 2, 20)
                    
                    if problem_type == "classification":
                        model = RandomForestClassifier(
                            n_estimators=n_estimators,
                            max_depth=max_depth,
                            min_samples_split=min_samples_split,
                            random_state=42
                        )
                    else:
                        model = RandomForestRegressor(
                            n_estimators=n_estimators,
                            max_depth=max_depth,
                            min_samples_split=min_samples_split,
                            random_state=42
                        )
                
                elif model_name == "XGBoost":
                    # Import XGBoost if available
                    from xgboost import XGBClassifier, XGBRegressor
                    
                    learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)
                    n_estimators = trial.suggest_int("n_estimators", 10, 100)
                    max_depth = trial.suggest_int("max_depth", 1, 10)
                    subsample = trial.suggest_float("subsample", 0.5, 1.0)
                    
                    if problem_type == "classification":
                        model = XGBClassifier(
                            learning_rate=learning_rate,
                            n_estimators=n_estimators,
                            max_depth=max_depth,
                            subsample=subsample,
                            random_state=42
                        )
                    else:
                        model = XGBRegressor(
                            learning_rate=learning_rate,
                            n_estimators=n_estimators,
                            max_depth=max_depth,
                            subsample=subsample,
                            random_state=42
                        )
                
                else:
                    # Default to basic Random Forest
                    n_estimators = trial.suggest_int("n_estimators", 10, 100)
                    max_depth = trial.suggest_int("max_depth", 1, 10)
                    
                    if problem_type == "classification":
                        model = RandomForestClassifier(
                            n_estimators=n_estimators,
                            max_depth=max_depth,
                            random_state=42
                        )
                    else:
                        model = RandomForestRegressor(
                            n_estimators=n_estimators,
                            max_depth=max_depth,
                            random_state=42
                        )
                
                # Perform cross-validation
                scores = cross_val_score(model, X_train, y_train, cv=3, 
                                        scoring='accuracy' if problem_type == 'classification' else 'r2')
                return scores.mean()
            
            # Create study and optimize
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=20)
            
            # Train final model with best parameters
            best_params = study.best_params
            if model_name == "XGBoost":
                from xgboost import XGBClassifier, XGBRegressor
                if problem_type == "classification":
                    best_model = XGBClassifier(**best_params, random_state=42)
                else:
                    best_model = XGBRegressor(**best_params, random_state=42)
            else:  # Random Forest
                if problem_type == "classification":
                    best_model = RandomForestClassifier(**best_params, random_state=42)
                else:
                    best_model = RandomForestRegressor(**best_params, random_state=42)
            
            best_model.fit(X_train, y_train)
            y_pred = best_model.predict(X_test)
            
            # Calculate metrics
            if problem_type == "classification":
                metrics = {
                    "accuracy": accuracy_score(y_test, y_pred),
                    "precision": precision_score(y_test, y_pred, average='weighted', zero_division=0),
                    "recall": recall_score(y_test, y_pred, average='weighted', zero_division=0),
                    "f1": f1_score(y_test, y_pred, average='weighted', zero_division=0)
                }
            else:
                metrics = {
                    "mse": mean_squared_error(y_test, y_pred),
                    "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                    "mae": mean_absolute_error(y_test, y_pred),
                    "r2": r2_score(y_test, y_pred)
                }
            
            return {
                "best_params": best_params,
                "best_score": study.best_value,
                "model": best_model,
                "metrics": metrics,
                "study": study
            }
        
        except ImportError:
            st.warning("Optuna not available for hyperparameter tuning. Please install it with 'pip install optuna'")
            # Return basic model training without optimization
            result = MLModeler.train_model(X_train, X_test, y_train, y_test, model_name, problem_type)
            return {"model": result["model"], "metrics": result["metrics"], "optimized": False}

    @staticmethod
    def ensemble_prediction(df: pd.DataFrame, target_col: str, 
                           ensemble_models: List[str] = None) -> Dict:
        """
        Create an ensemble prediction using multiple models
        """
        if ensemble_models is None:
            ensemble_models = ["Random Forest", "Gradient Boosting", "SVM"]
        
        # Prepare data
        X_train, X_test, y_test, y_train, problem_type, scaler, encoder = MLModeler.prepare_data(
            df, target_col, test_size=0.2
        )
        
        # Train individual models
        trained_models = {}
        predictions = {}
        
        for model_name in ensemble_models:
            if model_name in MLModeler.CLASSIFICATION_MODELS and problem_type == "classification":
                model = MLModeler.CLASSIFICATION_MODELS[model_name]
            elif model_name in MLModeler.REGRESSION_MODELS and problem_type == "regression":
                model = MLModeler.REGRESSION_MODELS[model_name]
            else:
                continue  # Skip incompatible models
                
            # Skip if advanced model not installed
            if isinstance(model, str) and model.endswith("_not_installed"):
                continue
            
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            
            trained_models[model_name] = model
            predictions[model_name] = pred
        
        if not predictions:
            raise ValueError("No valid models for ensemble prediction")
        
        # Average predictions for ensemble
        ensemble_pred = np.mean(list(predictions.values()), axis=0)
        
        # Calculate metrics
        if problem_type == "classification":
            metrics = {
                "accuracy": accuracy_score(y_test, ensemble_pred.round()),
                "precision": precision_score(y_test, ensemble_pred.round(), average='weighted', zero_division=0),
                "recall": recall_score(y_test, ensemble_pred.round(), average='weighted', zero_division=0),
                "f1": f1_score(y_test, ensemble_pred.round(), average='weighted', zero_division=0)
            }
        else:
            metrics = {
                "mse": mean_squared_error(y_test, ensemble_pred),
                "rmse": np.sqrt(mean_squared_error(y_test, ensemble_pred)),
                "mae": mean_absolute_error(y_test, ensemble_pred),
                "r2": r2_score(y_test, ensemble_pred)
            }
        
        return {
            "trained_models": trained_models,
            "predictions": predictions,
            "ensemble_prediction": ensemble_pred,
            "metrics": metrics,
            "problem_type": problem_type
        }