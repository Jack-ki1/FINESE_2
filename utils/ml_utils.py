import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler,
    OneHotEncoder, OrdinalEncoder, LabelEncoder
)
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC, SVR
import joblib
import logging
from typing import Dict, Tuple, Callable, Any

from .data_utils import (
    get_numeric_columns,
    get_categorical_columns,
    get_datetime_columns,
)
import warnings

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# -------- Optional dependency availability flags --------
try:
    import shap  # noqa: F401
    SHAP_AVAILABLE = True
except Exception:
    SHAP_AVAILABLE = False

try:
    from xgboost import XGBClassifier, XGBRegressor  # noqa: F401
    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False

try:
    from lightgbm import LGBMClassifier, LGBMRegressor  # noqa: F401
    LGBM_AVAILABLE = True
except Exception:
    LGBM_AVAILABLE = False

try:
    from catboost import CatBoostClassifier, CatBoostRegressor  # noqa: F401
    CATBOOST_AVAILABLE = True
except Exception:
    CATBOOST_AVAILABLE = False

try:
    from imblearn.over_sampling import SMOTE  # noqa: F401
    IMBLEARN_AVAILABLE = True
except Exception:
    IMBLEARN_AVAILABLE = False

try:
    import optuna  # noqa: F401
    OPTUNA_AVAILABLE = True
except Exception:
    OPTUNA_AVAILABLE = False

def model_key_to_estimator(model_key: str, problem_type: str):
    """Convert model key string to estimator instance."""
    models = {
        "RandomForest": RandomForestClassifier(random_state=42),
        "LogisticRegression": LogisticRegression(random_state=42, max_iter=1000),
        "DecisionTree": DecisionTreeClassifier(random_state=42),
        "KNN": KNeighborsClassifier(),
        "SVM": SVC(random_state=42),
        "NaiveBayes": GaussianNB(),
        "RandomForestReg": RandomForestRegressor(random_state=42),
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(random_state=42),
        "Lasso": Lasso(random_state=42),
        "DecisionTreeReg": DecisionTreeRegressor(random_state=42),
        "KNNReg": KNeighborsRegressor(),
        "SVR": SVR(),
    }

    if model_key in models:
        return models[model_key]

    # Optional boosters
    if model_key == "XGBoost":
        if not XGB_AVAILABLE:
            raise ValueError("XGBoost not available. Install xgboost.")
        return XGBClassifier(random_state=42, eval_metric="logloss")
    if model_key == "XGBoostReg":
        if not XGB_AVAILABLE:
            raise ValueError("XGBoost not available. Install xgboost.")
        return XGBRegressor(random_state=42)

    if model_key == "LightGBM":
        if not LGBM_AVAILABLE:
            raise ValueError("LightGBM not available. Install lightgbm.")
        return LGBMClassifier(random_state=42)
    if model_key == "LightGBMReg":
        if not LGBM_AVAILABLE:
            raise ValueError("LightGBM not available. Install lightgbm.")
        return LGBMRegressor(random_state=42)

    if model_key == "CatBoost":
        if not CATBOOST_AVAILABLE:
            raise ValueError("CatBoost not available. Install catboost.")
        return CatBoostClassifier(random_state=42, verbose=False)
    if model_key == "CatBoostReg":
        if not CATBOOST_AVAILABLE:
            raise ValueError("CatBoost not available. Install catboost.")
        return CatBoostRegressor(random_state=42, verbose=False)

    raise ValueError(f"Unknown model key: {model_key}")

def build_preprocessor(
    df: pd.DataFrame,
    target_col: str,
    encoding_strategy: str = "onehot",
    scaling_method: str = "standard",
    poly_degree: int = 1,
    include_interactions: bool = False
) -> Tuple[ColumnTransformer, list, list, Callable]:
    """
    Build a preprocessor for ML pipelines.
    
    Args:
        df: Input dataframe
        target_col: Name of target column to exclude from features
        encoding_strategy: How to encode categorical variables ('onehot', 'ordinal', 'target_encoding')
        scaling_method: How to scale numerical variables ('standard', 'minmax', 'robust', 'maxabs', 'none')
        poly_degree: Degree of polynomial features to generate
        include_interactions: Whether to include interaction features
    
    Returns:
        Tuple of (preprocessor, numeric_cols, categorical_cols, feature_names_getter)
    """
    # Identify feature columns
    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols]
    
    numeric_cols = get_numeric_columns(X)
    cat_cols = get_categorical_columns(X)
    
    # Handle case where both are empty
    if not numeric_cols and not cat_cols:
        # If no numeric or categorical columns, treat everything as numeric (for cases like datetime)
        numeric_cols = feature_cols
        cat_cols = []
    
    # Preprocessing transformers
    transformers = []
    
    if numeric_cols:
        # Build numeric pipeline
        numeric_steps = []
        
        # Imputation
        numeric_steps.append(('imputer', SimpleImputer(strategy='median')))
        
        # Scaling
        if scaling_method == "standard":
            numeric_steps.append(('scaler', StandardScaler()))
        elif scaling_method == "minmax":
            numeric_steps.append(('scaler', MinMaxScaler()))
        elif scaling_method == "robust":
            numeric_steps.append(('scaler', RobustScaler()))
        elif scaling_method == "maxabs":
            numeric_steps.append(('scaler', MaxAbsScaler()))
        
        # Polynomial features
        if poly_degree > 1:
            from sklearn.preprocessing import PolynomialFeatures
            numeric_steps.append(('poly', PolynomialFeatures(degree=poly_degree, include_bias=False)))
        
        # Interaction features
        if include_interactions and len(numeric_cols) > 1:
            from sklearn.preprocessing import PolynomialFeatures
            numeric_steps.append(('interactions', PolynomialFeatures(
                degree=2, 
                interaction_only=True, 
                include_bias=False
            )))
        
        transformers.append(('num', Pipeline(numeric_steps), numeric_cols))
    
    if cat_cols:
        # Build categorical pipeline
        cat_steps = []
        
        # Imputation (fill with mode)
        cat_steps.append(('imputer', SimpleImputer(strategy='constant', fill_value='missing')))
        
        # Encoding
        if encoding_strategy == "onehot":
            cat_steps.append(('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)))
        elif encoding_strategy == "ordinal":
            cat_steps.append(('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)))
        # Note: Target encoding is handled separately
        
        transformers.append(('cat', Pipeline(cat_steps), cat_cols))
    
    # Create the preprocessor
    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder='drop'  # Drop columns not specified in transformers
    )
    
    # Helper function to get feature names after transformation
    def get_feature_names(preprocessor):
        """Get feature names after preprocessing."""
        feature_names = []
        
        for name, transformer, columns in preprocessor.transformers_:
            if name == 'num':
                # For numeric features, names stay the same initially
                # But if polynomial features are used, they get transformed
                if hasattr(transformer.named_steps.get('poly'), 'get_feature_names_out'):
                    poly_features = transformer.named_steps['poly'].get_feature_names_out(columns)
                    feature_names.extend(poly_features)
                elif hasattr(transformer.named_steps.get('interactions'), 'get_feature_names_out'):
                    interaction_features = transformer.named_steps['interactions'].get_feature_names_out(columns)
                    feature_names.extend(interaction_features)
                else:
                    feature_names.extend(columns)
            elif name == 'cat':
                encoder = transformer.named_steps.get('encoder')
                if encoder and hasattr(encoder, 'get_feature_names_out'):
                    encoded_features = encoder.get_feature_names_out(columns)
                    feature_names.extend(encoded_features)
                else:
                    feature_names.extend(columns)
        
        return feature_names
    
    return preprocessor, numeric_cols, cat_cols, get_feature_names

def target_encode_column(series: pd.Series, target: pd.Series, smoothing: float = 1.0):
    """
    Perform target encoding on a categorical series with smoothing.
    
    Args:
        series: Categorical series to encode
        target: Target series for encoding
        smoothing: Smoothing factor (higher values = more smoothing toward global mean)
    
    Returns:
        Encoded series
    """
    # Calculate global mean
    global_mean = target.mean()
    
    # Calculate category means and counts
    category_stats = pd.DataFrame({
        'mean': target.groupby(series).mean(),
        'count': target.groupby(series).count()
    })
    
    # Apply smoothing: weighted average of category mean and global mean
    def smoothed_encoding(row):
        if row.name in category_stats.index:
            cat_mean = category_stats.loc[row.name, 'mean']
            cat_count = category_stats.loc[row.name, 'count']
            # Weighted average: more weight to category mean as count increases
            weight = cat_count / (cat_count + smoothing)
            return weight * cat_mean + (1 - weight) * global_mean
        else:
            # For unseen categories, use global mean
            return global_mean
    
    return series.map(smoothed_encoding)

def generate_code_snippet(pipeline, X, y, problem_type: str, feature_names: list, target_name: str):
    """
    Generate a Python code snippet that reproduces the trained pipeline.
    
    Args:
        pipeline: Trained sklearn pipeline
        X: Feature data used for training
        y: Target data used for training
        problem_type: 'classification' or 'regression'
        feature_names: Names of features
        target_name: Name of target column
    
    Returns:
        String containing Python code
    """
    # This is a simplified version - in a real implementation, we would extract
    # the actual steps and parameters from the pipeline
    code = f"""
# Generated code to reproduce the model
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForest{'' if problem_type == 'classification' else 'Reg'}ator

# Load your data
# df = pd.read_csv('your_data.csv')

# Define features and target
X = df[{feature_names}]  # Your feature columns
y = df['{target_name}']  # Your target column

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define the model (you'll need to reconstruct the actual pipeline)
model = RandomForest{'' if problem_type == 'classification' else 'Reg'}ator(random_state=42)
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)

# Evaluate
from sklearn.metrics import {f"accuracy_score, classification_report" if problem_type == 'classification' else 'r2_score, mean_squared_error'}
"""
    if problem_type == 'classification':
        code += """
accuracy = accuracy_score(y_test, predictions)
print(f"Accuracy: {{accuracy}}")
"""
    else:
        code += """
r2 = r2_score(y_test, predictions)
print(f"R2 Score: {r2}")
"""
    
    return code