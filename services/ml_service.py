"""ML Service Module - Handles machine learning model training and evaluation functionality."""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score, classification_report
import logging
from typing import Dict, Any, Tuple, List, Optional
import pickle
import os

logger = logging.getLogger(__name__)

def prepare_ml_data(df: pd.DataFrame, target_col: str, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare data for machine learning by splitting features and target.
    
    Args:
        df: Input DataFrame
        target_col: Name of the target column
        test_size: Proportion of data to use for testing
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame")
    
    # Separate features and target
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    
    return X_train, X_test, y_train, y_test


def create_preprocessing_pipeline(X_train: pd.DataFrame, problem_type: str = 'classification') -> ColumnTransformer:
    """
    Create a preprocessing pipeline for ML tasks.
    
    Args:
        X_train: Training features
        problem_type: Type of problem ('classification' or 'regression')
        
    Returns:
        ColumnTransformer pipeline
    """
    # Identify numeric and categorical columns
    numeric_features = X_train.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Create preprocessing pipelines
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # Combine preprocessing steps
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    
    return preprocessor


def train_model(X_train: pd.DataFrame, y_train: pd.Series, problem_type: str = 'classification', 
                algorithm: str = 'random_forest') -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Train a machine learning model.
    
    Args:
        X_train: Training features
        y_train: Training targets
        problem_type: Type of problem ('classification' or 'regression')
        algorithm: Algorithm to use ('random_forest', 'logistic_regression', 'linear_regression')
        
    Returns:
        Tuple of (trained_model_pipeline, model_metadata)
    """
    # Determine if it's a classification or regression problem
    is_classification = problem_type == 'classification'
    
    # Select appropriate model based on problem type and algorithm
    if is_classification:
        if algorithm == 'random_forest':
            model = RandomForestClassifier(random_state=42, n_estimators=100)
        elif algorithm == 'logistic_regression':
            model = LogisticRegression(random_state=42, max_iter=1000)
        else:
            model = RandomForestClassifier(random_state=42, n_estimators=100)  # Default
    else:  # regression
        if algorithm == 'random_forest':
            model = RandomForestRegressor(random_state=42, n_estimators=100)
        elif algorithm == 'linear_regression':
            model = LinearRegression()
        else:
            model = RandomForestRegressor(random_state=42, n_estimators=100)  # Default
    
    # Create preprocessing pipeline
    preprocessor = create_preprocessing_pipeline(X_train, problem_type)
    
    # Create full pipeline
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier' if is_classification else 'regressor', model)
    ])
    
    # Fit the pipeline
    pipeline.fit(X_train, y_train)
    
    # Prepare metadata
    metadata = {
        'problem_type': problem_type,
        'algorithm': algorithm,
        'feature_names': list(X_train.columns),
        'target_values': y_train.unique().tolist() if is_classification else None,
        'training_samples': len(X_train)
    }
    
    return pipeline, metadata


def evaluate_model(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series, 
                   problem_type: str = 'classification') -> Dict[str, Any]:
    """
    Evaluate a trained model.
    
    Args:
        pipeline: Trained model pipeline
        X_test: Test features
        y_test: Test targets
        problem_type: Type of problem ('classification' or 'regression')
        
    Returns:
        Dictionary containing evaluation metrics
    """
    # Predictions
    y_pred = pipeline.predict(X_test)
    
    # Compute metrics based on problem type
    if problem_type == 'classification':
        accuracy = accuracy_score(y_test, y_pred)
        
        # Detailed classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        metrics = {
            'accuracy': accuracy,
            'classification_report': report,
            'f1_score': report['weighted avg']['f1-score'] if 'weighted avg' in report else None,
            'precision': report['weighted avg']['precision'] if 'weighted avg' in report else None,
            'recall': report['weighted avg']['recall'] if 'weighted avg' in report else None
        }
    else:  # regression
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'r2_score': r2
        }
    
    return metrics


def predict_with_model(pipeline: Pipeline, X_new: pd.DataFrame) -> np.ndarray:
    """
    Make predictions with a trained model.
    
    Args:
        pipeline: Trained model pipeline
        X_new: New features for prediction
        
    Returns:
        Array of predictions
    """
    predictions = pipeline.predict(X_new)
    return predictions


def save_model(pipeline: Pipeline, filepath: str) -> bool:
    """
    Save a trained model to disk.
    
    Args:
        pipeline: Trained model pipeline
        filepath: Path to save the model
        
    Returns:
        Boolean indicating success
    """
    try:
        with open(filepath, 'wb') as f:
            pickle.dump(pipeline, f)
        logger.info(f"Model saved successfully to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        return False


def load_model(filepath: str) -> Optional[Pipeline]:
    """
    Load a trained model from disk.
    
    Args:
        filepath: Path to load the model from
        
    Returns:
        Loaded model pipeline or None if failed
    """
    if not os.path.exists(filepath):
        logger.error(f"Model file does not exist: {filepath}")
        return None
    
    try:
        with open(filepath, 'rb') as f:
            pipeline = pickle.load(f)
        logger.info(f"Model loaded successfully from {filepath}")
        return pipeline
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None