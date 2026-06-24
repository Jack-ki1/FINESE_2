"""
FINESE2 - Consolidated ML Models Module
Comprehensive machine learning algorithms and model management in a single module.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
import logging
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.svm import SVC, SVR
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
import joblib
import pickle
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class MLModelManager:
    """
    Consolidated ML model manager providing comprehensive machine learning capabilities.
    """
    
    def __init__(self):
        self.models = {}
        self.model_configs = {}
        self.scalers = {}
        self.label_encoders = {}
        self.available_models = {
            'classification': {
                'logistic_regression': LogisticRegression,
                'random_forest': RandomForestClassifier,
                'decision_tree': DecisionTreeClassifier,
                'svm': SVC,
                'gradient_boosting': GradientBoostingClassifier,
                'naive_bayes': GaussianNB
            },
            'regression': {
                'linear_regression': LinearRegression,
                'ridge': Ridge,
                'lasso': Lasso,
                'random_forest': RandomForestRegressor,
                'decision_tree': DecisionTreeRegressor,
                'svm': SVR,
                'gradient_boosting': GradientBoostingRegressor
            }
        }
    
    def prepare_data(self, df: pd.DataFrame, target_column: str, 
                     feature_columns: Optional[List[str]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for modeling by separating features and target."""
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame")
        
        if feature_columns is None:
            # Use all columns except the target
            feature_columns = [col for col in df.columns if col != target_column]
        
        X = df[feature_columns].copy()
        y = df[target_column].copy()
        
        # Handle categorical variables
        categorical_features = X.select_dtypes(include=['object', 'category']).columns
        for col in categorical_features:
            if col not in self.label_encoders:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.label_encoders[col] = le
            else:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
        
        # Handle missing values
        X = X.fillna(X.mean())
        y = y.fillna(y.mean()) if y.dtype in ['float64', 'int64'] else y.fillna(y.mode()[0])
        
        return X.values, y.values
    
    def split_data(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2, 
                   random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into training and testing sets."""
        return train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    def identify_problem_type(self, y: np.ndarray) -> str:
        """Automatically identify if the problem is classification or regression."""
        unique_values = len(np.unique(y))
        total_values = len(y)
        
        # If less than 10% of values are unique and less than 20 unique values, consider it classification
        if (unique_values / total_values < 0.05) and (unique_values < 20):
            return 'classification'
        else:
            return 'regression'
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                   model_type: str, problem_type: str = 'auto', 
                   hyperparameters: Optional[Dict] = None) -> Any:
        """Train a model with specified parameters."""
        if problem_type == 'auto':
            problem_type = self.identify_problem_type(y_train)
        
        if problem_type not in self.available_models:
            raise ValueError(f"Problem type '{problem_type}' not supported")
        
        if model_type not in self.available_models[problem_type]:
            raise ValueError(f"Model type '{model_type}' not available for {problem_type}")
        
        # Get the model class
        model_class = self.available_models[problem_type][model_type]
        
        # Set default hyperparameters if none provided
        if hyperparameters is None:
            hyperparameters = {}
        
        # Create and train the model
        model = model_class(**hyperparameters)
        model.fit(X_train, y_train)
        
        return model
    
    def evaluate_model(self, model: Any, X_test: np.ndarray, y_test: np.ndarray, 
                      problem_type: str) -> Dict[str, float]:
        """Evaluate the trained model."""
        y_pred = model.predict(X_test)
        
        if problem_type == 'classification':
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
                'f1_score': f1_score(y_test, y_pred, average='weighted', zero_division=0)
            }
            
            # Add ROC AUC if binary classification
            unique_classes = len(np.unique(y_test))
            if unique_classes == 2:
                try:
                    y_pred_proba = model.predict_proba(X_test)[:, 1]
                    metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba)
                except AttributeError:
                    # Some models don't have predict_proba
                    pass
        elif problem_type == 'regression':
            metrics = {
                'mse': mean_squared_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'mae': mean_absolute_error(y_test, y_pred),
                'r2_score': r2_score(y_test, y_pred)
            }
        else:
            raise ValueError(f"Unknown problem type: {problem_type}")
        
        return metrics
    
    def cross_validate_model(self, model: Any, X: np.ndarray, y: np.ndarray, 
                            cv: int = 5) -> Dict[str, float]:
        """Perform cross-validation on the model."""
        scores = cross_val_score(model, X, y, cv=cv)
        
        return {
            'cv_mean_score': scores.mean(),
            'cv_std_score': scores.std(),
            'cv_scores': scores.tolist()
        }
    
    def hyperparameter_tuning(self, X_train: np.ndarray, y_train: np.ndarray,
                             model_type: str, problem_type: str,
                             param_grid: Dict[str, List]) -> Tuple[Any, Dict]:
        """Perform hyperparameter tuning using GridSearchCV."""
        if problem_type not in self.available_models:
            raise ValueError(f"Problem type '{problem_type}' not supported")
        
        if model_type not in self.available_models[problem_type]:
            raise ValueError(f"Model type '{model_type}' not available for {problem_type}")
        
        model_class = self.available_models[problem_type][model_type]
        model = model_class()
        
        grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy' if problem_type == 'classification' else 'r2')
        grid_search.fit(X_train, y_train)
        
        return grid_search.best_estimator_, grid_search.best_params_
    
    def compare_models(self, X_train: np.ndarray, y_train: np.ndarray, 
                      X_test: np.ndarray, y_test: np.ndarray,
                      model_types: List[str], problem_type: str) -> Dict[str, Dict]:
        """Compare multiple models and return their performance."""
        results = {}
        
        for model_type in model_types:
            try:
                # Train the model
                model = self.train_model(X_train, y_train, model_type, problem_type)
                
                # Evaluate the model
                metrics = self.evaluate_model(model, X_test, y_test, problem_type)
                
                # Perform cross-validation
                cv_results = self.cross_validate_model(model, X_train, y_train)
                
                results[model_type] = {
                    'model': model,
                    'metrics': metrics,
                    'cross_validation': cv_results
                }
            except Exception as e:
                logger.error(f"Error training model {model_type}: {str(e)}")
                results[model_type] = {
                    'error': str(e)
                }
        
        return results
    
    def get_feature_importance(self, model: Any, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from the trained model if available."""
        importance_dict = {}
        
        if hasattr(model, 'feature_importances_'):
            # Tree-based models
            importances = model.feature_importances_
            for i, feature in enumerate(feature_names):
                importance_dict[feature] = importances[i]
        elif hasattr(model, 'coef_'):
            # Linear models
            coefs = model.coef_
            if len(coefs.shape) > 1:  # Multiclass
                coefs = np.mean(np.abs(coefs), axis=0)
            else:
                coefs = np.abs(coefs)
            
            for i, feature in enumerate(feature_names):
                importance_dict[feature] = coefs[i]
        else:
            # Model doesn't support feature importance
            importance_dict = {"error": "Model does not support feature importance"}
        
        return importance_dict
    
    def make_predictions(self, model: Any, X: np.ndarray) -> np.ndarray:
        """Make predictions using the trained model."""
        return model.predict(X)
    
    def save_model(self, model: Any, model_name: str, model_path: str = './models/') -> str:
        """Save the trained model to disk."""
        os.makedirs(model_path, exist_ok=True)
        model_filename = f"{model_path}{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        
        with open(model_filename, 'wb') as f:
            pickle.dump(model, f)
        
        # Store model reference
        self.models[model_name] = model_filename
        
        return model_filename
    
    def load_model(self, model_filename: str) -> Any:
        """Load a trained model from disk."""
        with open(model_filename, 'rb') as f:
            model = pickle.load(f)
        
        return model
    
    def train_pipeline(self, df: pd.DataFrame, target_column: str, 
                      model_type: str, problem_type: str = 'auto',
                      feature_columns: Optional[List[str]] = None,
                      test_size: float = 0.2) -> Dict[str, Any]:
        """Complete training pipeline from data to model."""
        # Prepare data
        X, y = self.prepare_data(df, target_column, feature_columns)
        
        # Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y, test_size)
        
        # Identify problem type if auto
        if problem_type == 'auto':
            problem_type = self.identify_problem_type(y)
        
        # Train model
        model = self.train_model(X_train, y_train, model_type, problem_type)
        
        # Evaluate model
        metrics = self.evaluate_model(model, X_test, y_test, problem_type)
        
        # Cross-validate
        cv_results = self.cross_validate_model(model, X_train, y_train)
        
        # Get feature importance if available
        feature_names = feature_columns or [col for col in df.columns if col != target_column]
        feature_importance = self.get_feature_importance(model, feature_names)
        
        return {
            'model': model,
            'metrics': metrics,
            'cross_validation': cv_results,
            'feature_importance': feature_importance,
            'X_test': X_test,
            'y_test': y_test,
            'y_pred': model.predict(X_test)
        }
    
    def get_available_models(self, problem_type: str = None) -> Dict[str, List[str]]:
        """Get list of available models."""
        if problem_type:
            if problem_type in self.available_models:
                return {problem_type: list(self.available_models[problem_type].keys())}
            else:
                raise ValueError(f"Unknown problem type: {problem_type}")
        else:
            return {ptype: list(models.keys()) for ptype, models in self.available_models.items()}
    
    def get_model_summary(self, model: Any) -> str:
        """Get a summary of the model."""
        if hasattr(model, 'get_params'):
            params = model.get_params()
            return f"Model: {type(model).__name__}, Parameters: {len(params)}"
        else:
            return f"Model: {type(model).__name__}"


# Global instance
ml_model_manager = MLModelManager()