from flask import Blueprint, render_template, session, jsonify, request, current_app
import uuid
import threading
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                            mean_squared_error, r2_score, mean_absolute_error, 
                            confusion_matrix, classification_report, roc_auc_score,
                            mean_absolute_percentage_error, explained_variance_score)
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler, RobustScaler
from sklearn.pipeline import Pipeline
# Enable experimental imputers
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import KNNImputer, IterativeImputer
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from scipy import stats
import json
import plotly.utils
import time
import difflib

from datetime import datetime

bp = Blueprint('ml', __name__)
jobs = {}

# Model registry for storing trained models
model_registry = {}

def get_scaler(scaler_type='standard'):
    """Get scaler based on type"""
    scalers = {
        'standard': StandardScaler(),
        'minmax': MinMaxScaler(),
        'robust': RobustScaler()
    }
    return scalers.get(scaler_type, StandardScaler())

def optimize_with_optuna(X_train, y_train, task, algorithm, n_trials=50):
    """Enhanced Optuna hyperparameter optimization with more algorithms and better search spaces"""
    try:
        import optuna
        
        def objective(trial):
            if task == 'classification':
                if algorithm in ['rf', 'xgboost', 'lightgbm', 'catboost']:
                    if algorithm == 'rf':
                        params = {
                            'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                            'max_depth': trial.suggest_int('max_depth', 3, 30),
                            'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                            'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
                        }
                        from sklearn.ensemble import RandomForestClassifier
                        model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)
                    
                    elif algorithm == 'xgboost':
                        try:
                            import xgboost as xgb
                            params = {
                                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                                'max_depth': trial.suggest_int('max_depth', 3, 12),
                                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                                'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                                'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True)
                            }
                            model = xgb.XGBClassifier(**params, random_state=42, use_label_encoder=False, eval_metric='logloss')
                        except ImportError:
                            from sklearn.ensemble import GradientBoostingClassifier
                            model = GradientBoostingClassifier(random_state=42)
                    
                    elif algorithm == 'lightgbm':
                        try:
                            import lightgbm as lgb
                            params = {
                                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                                'max_depth': trial.suggest_int('max_depth', 3, 12),
                                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                                'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                                'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                                'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True)
                            }
                            model = lgb.LGBMClassifier(**params, random_state=42, verbose=-1)
                        except ImportError:
                            from sklearn.ensemble import GradientBoostingClassifier
                            model = GradientBoostingClassifier(random_state=42)
                    
                    else:  # catboost
                        try:
                            from catboost import CatBoostClassifier
                            params = {
                                'iterations': trial.suggest_int('iterations', 100, 1000),
                                'depth': trial.suggest_int('depth', 3, 12),
                                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                                'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1e-8, 10.0, log=True)
                            }
                            model = CatBoostClassifier(**params, random_state=42, verbose=0)
                        except ImportError:
                            from sklearn.ensemble import GradientBoostingClassifier
                            model = GradientBoostingClassifier(random_state=42)
                
                elif algorithm == 'gb':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                        'max_depth': trial.suggest_int('max_depth', 3, 12),
                        'subsample': trial.suggest_float('subsample', 0.6, 1.0)
                    }
                    from sklearn.ensemble import GradientBoostingClassifier
                    model = GradientBoostingClassifier(**params, random_state=42)
                
                elif algorithm == 'svm':
                    params = {
                        'C': trial.suggest_float('C', 0.1, 100, log=True),
                        'gamma': trial.suggest_categorical('gamma', ['scale', 'auto']),
                        'kernel': trial.suggest_categorical('kernel', ['rbf', 'linear', 'poly'])
                    }
                    from sklearn.svm import SVC
                    model = SVC(**params, random_state=42, probability=True)
                
                elif algorithm == 'lr':
                    params = {
                        'C': trial.suggest_float('C', 0.01, 100, log=True),
                        'penalty': trial.suggest_categorical('penalty', ['l1', 'l2', 'elasticnet']),
                        'solver': trial.suggest_categorical('solver', ['liblinear', 'saga'])
                    }
                    from sklearn.linear_model import LogisticRegression
                    model = LogisticRegression(**params, random_state=42, max_iter=1000)
                
                else:
                    from sklearn.ensemble import RandomForestClassifier
                    model = RandomForestClassifier(random_state=42)
                
                X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42, stratify=y_train if len(np.unique(y_train)) > 1 else None)
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                
                # Use F1 score for better balance
                return f1_score(y_val, y_pred, average='weighted', zero_division=0)
            
            elif task == 'regression':
                if algorithm in ['rf_reg', 'xgboost_reg', 'lightgbm_reg']:
                    if algorithm == 'rf_reg':
                        params = {
                            'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                            'max_depth': trial.suggest_int('max_depth', 3, 30),
                            'min_samples_split': trial.suggest_int('min_samples_split', 2, 20)
                        }
                        from sklearn.ensemble import RandomForestRegressor
                        model = RandomForestRegressor(**params, random_state=42, n_jobs=-1)
                    
                    elif algorithm == 'xgboost_reg':
                        try:
                            import xgboost as xgb
                            params = {
                                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                                'max_depth': trial.suggest_int('max_depth', 3, 12),
                                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0)
                            }
                            model = xgb.XGBRegressor(**params, random_state=42)
                        except ImportError:
                            from sklearn.ensemble import GradientBoostingRegressor
                            model = GradientBoostingRegressor(random_state=42)
                    
                    else:  # lightgbm_reg
                        try:
                            import lightgbm as lgb
                            params = {
                                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                                'max_depth': trial.suggest_int('max_depth', 3, 12),
                                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                                'num_leaves': trial.suggest_int('num_leaves', 20, 100)
                            }
                            model = lgb.LGBMRegressor(**params, random_state=42, verbose=-1)
                        except ImportError:
                            from sklearn.ensemble import GradientBoostingRegressor
                            model = GradientBoostingRegressor(random_state=42)
                
                elif algorithm == 'ridge':
                    params = {
                        'alpha': trial.suggest_float('alpha', 0.01, 100, log=True)
                    }
                    from sklearn.linear_model import Ridge
                    model = Ridge(**params, random_state=42)
                
                elif algorithm == 'lasso':
                    params = {
                        'alpha': trial.suggest_float('alpha', 0.01, 100, log=True)
                    }
                    from sklearn.linear_model import Lasso
                    model = Lasso(**params, random_state=42, max_iter=10000)
                
                elif algorithm == 'elasticnet':
                    params = {
                        'alpha': trial.suggest_float('alpha', 0.01, 100, log=True),
                        'l1_ratio': trial.suggest_float('l1_ratio', 0.0, 1.0)
                    }
                    from sklearn.linear_model import ElasticNet
                    model = ElasticNet(**params, random_state=42, max_iter=10000)
                
                else:
                    from sklearn.ensemble import RandomForestRegressor
                    model = RandomForestRegressor(random_state=42)
                
                X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                return -mean_squared_error(y_val, y_pred)  # Negative for minimization
            
            return 0
        
        study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler())
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        return study.best_params, study.best_value
        
    except ImportError:
        return {}, 0

def calculate_advanced_metrics(y_true, y_pred, task, model=None, X_test=None):
    """Calculate comprehensive evaluation metrics"""
    metrics = {}
    
    if task in ['classification', 'neural_classification']:
        metrics.update({
            'accuracy': accuracy_score(y_true, y_pred),
            'precision_macro': precision_score(y_true, y_pred, average='macro', zero_division=0),
            'precision_weighted': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall_macro': recall_score(y_true, y_pred, average='macro', zero_division=0),
            'recall_weighted': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_macro': f1_score(y_true, y_pred, average='macro', zero_division=0),
            'f1_weighted': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        })
        
        # ROC-AUC for binary/multiclass
        try:
            if hasattr(model, 'predict_proba'):
                y_prob = model.predict_proba(X_test)
                if y_prob.shape[1] == 2:
                    metrics['roc_auc'] = roc_auc_score(y_true, y_prob[:, 1])
                else:
                    metrics['roc_auc_ovr'] = roc_auc_score(y_true, y_prob, multi_class='ovr', average='weighted')
        except:
            pass
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        # Classification report
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        metrics['classification_report'] = report
    
    elif task in ['regression', 'neural_regression']:
        metrics.update({
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'mape': mean_absolute_percentage_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'explained_variance': explained_variance_score(y_true, y_pred),
            'median_absolute_error': np.median(np.abs(y_true - y_pred))
        })
        
        # Residuals analysis
        residuals = y_true - y_pred
        metrics['residuals'] = {
            'mean': float(np.mean(residuals)),
            'std': float(np.std(residuals)),
            'skewness': float(pd.Series(residuals).skew()),
            'kurtosis': float(pd.Series(residuals).kurtosis())
        }
    
    return metrics

@bp.route('/')
def ml_page():
    return render_template('ml.html', active_tab='ml')

@bp.route('/api/train', methods=['POST'])
def train():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    cfg = request.json
    target = cfg.get('target')
    task = cfg.get('task', 'classification')
    algorithm = cfg.get('algorithm', 'rf')
    test_size = cfg.get('test_size', 0.2)
    random_state = cfg.get('random_state', 42)
    enable_automl = cfg.get('automl', False)
    n_trials = cfg.get('n_trials', 50)
    scaler_type = cfg.get('scaler', 'standard')
    enable_cv = cfg.get('cross_validation', True)
    cv_folds = cfg.get('cv_folds', 5)
    
    if not target:
        return jsonify({'error': 'No target column specified'}), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'running', 
        'progress': 0, 
        'result': None,
        'started_at': datetime.now().isoformat()
    }
    session['ml_job_id'] = job_id
    
    def run_training():
        start_time = time.time()
        try:
            df, _ = current_app.dataset_store.load(dataset_id)
            
            # Update progress
            jobs[job_id]['progress'] = 5
            
            # Prepare data
            if task in ['classification', 'regression', 'neural_classification', 'neural_regression']:
                # Supervised learning
                X = df.drop(columns=[target])
                y = df[target]
                
                # Handle categorical features with advanced encoding
                categorical_cols = X.select_dtypes(include=['object']).columns
                label_encoders = {}
                for col in categorical_cols:
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
                    label_encoders[col] = le
                
                # Handle categorical target for classification
                target_encoder = None
                if task in ['classification', 'neural_classification']:
                    if y.dtype == 'object':
                        target_encoder = LabelEncoder()
                        y = target_encoder.fit_transform(y)
                
                jobs[job_id]['progress'] = 15
                
                # Train-test split with stratification for classification
                stratify_param = y if task in ['classification', 'neural_classification'] and len(np.unique(y)) > 1 else None
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=random_state, stratify=stratify_param
                )
                
                jobs[job_id]['progress'] = 20
                
                # Scale features
                scaler = get_scaler(scaler_type)
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                jobs[job_id]['progress'] = 25
                
                # AutoML optimization if enabled
                best_params = {}
                if enable_automl:
                    jobs[job_id]['progress'] = 30
                    best_params, best_score = optimize_with_optuna(
                        X_train_scaled, y_train, task, algorithm, n_trials
                    )
                    jobs[job_id]['progress'] = 40
                
                # Train model based on algorithm
                metrics = {}
                feature_importance = {}
                predictions = {}
                
                if task in ['classification', 'neural_classification']:
                    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier, ExtraTreesClassifier
                    from sklearn.linear_model import LogisticRegression
                    from sklearn.svm import SVC
                    from sklearn.neighbors import KNeighborsClassifier
                    from sklearn.tree import DecisionTreeClassifier
                    from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
                    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
                    from sklearn.neural_network import MLPClassifier
                    
                    # Try to import advanced gradient boosting libraries
                    try:
                        import xgboost as xgb
                        has_xgboost = True
                    except ImportError:
                        has_xgboost = False
                    
                    try:
                        import lightgbm as lgb
                        has_lightgbm = True
                    except ImportError:
                        has_lightgbm = False
                    
                    try:
                        from catboost import CatBoostClassifier
                        has_catboost = True
                    except ImportError:
                        has_catboost = False
                    
                    models = {
                        'rf': RandomForestClassifier(
                            n_estimators=best_params.get('n_estimators', 200), 
                            max_depth=best_params.get('max_depth', None),
                            min_samples_split=best_params.get('min_samples_split', 2),
                            min_samples_leaf=best_params.get('min_samples_leaf', 1),
                            max_features=best_params.get('max_features', 'sqrt'),
                            random_state=random_state,
                            n_jobs=-1
                        ),
                        'et': ExtraTreesClassifier(
                            n_estimators=best_params.get('n_estimators', 200),
                            max_depth=best_params.get('max_depth', None),
                            random_state=random_state,
                            n_jobs=-1
                        ),
                        'gb': GradientBoostingClassifier(
                            n_estimators=best_params.get('n_estimators', 200),
                            learning_rate=best_params.get('learning_rate', 0.1),
                            max_depth=best_params.get('max_depth', 5),
                            subsample=best_params.get('subsample', 0.8),
                            random_state=random_state
                        ),
                        'xgboost': xgb.XGBClassifier(
                            n_estimators=best_params.get('n_estimators', 200),
                            max_depth=best_params.get('max_depth', 6),
                            learning_rate=best_params.get('learning_rate', 0.1),
                            subsample=best_params.get('subsample', 0.8),
                            colsample_bytree=best_params.get('colsample_bytree', 0.8),
                            reg_alpha=best_params.get('reg_alpha', 0),
                            reg_lambda=best_params.get('reg_lambda', 1),
                            random_state=random_state,
                            use_label_encoder=False,
                            eval_metric='logloss',
                            n_jobs=-1
                        ) if has_xgboost else None,
                        'lightgbm': lgb.LGBMClassifier(
                            n_estimators=best_params.get('n_estimators', 200),
                            max_depth=best_params.get('max_depth', 6),
                            learning_rate=best_params.get('learning_rate', 0.1),
                            num_leaves=best_params.get('num_leaves', 31),
                            subsample=best_params.get('subsample', 0.8),
                            colsample_bytree=best_params.get('colsample_bytree', 0.8),
                            reg_alpha=best_params.get('reg_alpha', 0),
                            reg_lambda=best_params.get('reg_lambda', 1),
                            random_state=random_state,
                            verbose=-1,
                            n_jobs=-1
                        ) if has_lightgbm else None,
                        'catboost': CatBoostClassifier(
                            iterations=best_params.get('iterations', 200),
                            depth=best_params.get('depth', 6),
                            learning_rate=best_params.get('learning_rate', 0.1),
                            l2_leaf_reg=best_params.get('l2_leaf_reg', 3),
                            random_state=random_state,
                            verbose=0
                        ) if has_catboost else None,
                        'lr': LogisticRegression(
                            C=best_params.get('C', 1.0),
                            penalty=best_params.get('penalty', 'l2'),
                            solver=best_params.get('solver', 'liblinear'),
                            max_iter=1000, 
                            random_state=random_state
                        ),
                        'svm': SVC(
                            C=best_params.get('C', 1.0),
                            kernel=best_params.get('kernel', 'rbf'),
                            gamma=best_params.get('gamma', 'scale'),
                            probability=True,
                            random_state=random_state
                        ),
                        'knn': KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
                        'dt': DecisionTreeClassifier(
                            max_depth=best_params.get('max_depth', None),
                            min_samples_split=best_params.get('min_samples_split', 2),
                            random_state=random_state
                        ),
                        'nb': GaussianNB(),
                        'ada': AdaBoostClassifier(
                            n_estimators=best_params.get('n_estimators', 100),
                            random_state=random_state
                        ),
                        'lda': LinearDiscriminantAnalysis(),
                        'qda': QuadraticDiscriminantAnalysis(),
                        'mlp_class': MLPClassifier(
                            hidden_layer_sizes=(100, 50),
                            max_iter=1000,
                            random_state=random_state
                        )
                    }
                    
                    # Filter out None values (libraries not installed)
                    models = {k: v for k, v in models.items() if v is not None}
                    
                    model = models.get(algorithm, models['rf'])
                    
                    jobs[job_id]['progress'] = 50
                    
                    # Cross-validation if enabled
                    cv_scores = None
                    if enable_cv:
                        try:
                            scoring = 'f1_weighted' if len(np.unique(y_train)) > 2 else 'roc_auc'
                            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv_folds, scoring=scoring, n_jobs=-1)
                            jobs[job_id]['cv_scores'] = cv_scores.tolist()
                        except Exception as e:
                            jobs[job_id]['cv_error'] = str(e)
                    
                    jobs[job_id]['progress'] = 60
                    
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    
                    jobs[job_id]['progress'] = 70
                    
                    # Calculate advanced metrics
                    metrics = calculate_advanced_metrics(y_test, y_pred, task, model, X_test_scaled)
                    
                    jobs[job_id]['progress'] = 75
                    
                elif task in ['regression', 'neural_regression']:
                    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
                    from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet, HuberRegressor
                    from sklearn.svm import SVR
                    from sklearn.neighbors import KNeighborsRegressor
                    from sklearn.tree import DecisionTreeRegressor
                    from sklearn.neural_network import MLPRegressor
                    
                    # Try to import advanced gradient boosting libraries
                    try:
                        import xgboost as xgb
                        has_xgboost = True
                    except ImportError:
                        has_xgboost = False
                    
                    try:
                        import lightgbm as lgb
                        has_lightgbm = True
                    except ImportError:
                        has_lightgbm = False
                    
                    models = {
                        'rf_reg': RandomForestRegressor(
                            n_estimators=best_params.get('n_estimators', 200),
                            max_depth=best_params.get('max_depth', None),
                            min_samples_split=best_params.get('min_samples_split', 2),
                            random_state=random_state,
                            n_jobs=-1
                        ),
                        'et_reg': ExtraTreesRegressor(
                            n_estimators=best_params.get('n_estimators', 200),
                            max_depth=best_params.get('max_depth', None),
                            random_state=random_state,
                            n_jobs=-1
                        ),
                        'gb_reg': GradientBoostingRegressor(
                            n_estimators=best_params.get('n_estimators', 200),
                            learning_rate=best_params.get('learning_rate', 0.1),
                            max_depth=best_params.get('max_depth', 5),
                            subsample=best_params.get('subsample', 0.8),
                            random_state=random_state
                        ),
                        'xgboost_reg': xgb.XGBRegressor(
                            n_estimators=best_params.get('n_estimators', 200),
                            max_depth=best_params.get('max_depth', 6),
                            learning_rate=best_params.get('learning_rate', 0.1),
                            subsample=best_params.get('subsample', 0.8),
                            colsample_bytree=best_params.get('colsample_bytree', 0.8),
                            reg_alpha=best_params.get('reg_alpha', 0),
                            reg_lambda=best_params.get('reg_lambda', 1),
                            random_state=random_state,
                            n_jobs=-1
                        ) if has_xgboost else None,
                        'lightgbm_reg': lgb.LGBMRegressor(
                            n_estimators=best_params.get('n_estimators', 200),
                            max_depth=best_params.get('max_depth', 6),
                            learning_rate=best_params.get('learning_rate', 0.1),
                            num_leaves=best_params.get('num_leaves', 31),
                            subsample=best_params.get('subsample', 0.8),
                            colsample_bytree=best_params.get('colsample_bytree', 0.8),
                            reg_alpha=best_params.get('reg_alpha', 0),
                            reg_lambda=best_params.get('reg_lambda', 1),
                            random_state=random_state,
                            verbose=-1,
                            n_jobs=-1
                        ) if has_lightgbm else None,
                        'lr_reg': LinearRegression(),
                        'ridge': Ridge(alpha=best_params.get('alpha', 1.0), random_state=random_state),
                        'lasso': Lasso(alpha=best_params.get('alpha', 1.0), random_state=random_state, max_iter=10000),
                        'elastic': ElasticNet(
                            alpha=best_params.get('alpha', 1.0),
                            l1_ratio=best_params.get('l1_ratio', 0.5),
                            random_state=random_state,
                            max_iter=10000
                        ),
                        'huber': HuberRegressor(max_iter=1000),
                        'svr': SVR(kernel='rbf', C=best_params.get('C', 1.0)),
                        'knn_reg': KNeighborsRegressor(n_neighbors=5, n_jobs=-1),
                        'dt_reg': DecisionTreeRegressor(
                            max_depth=best_params.get('max_depth', None),
                            min_samples_split=best_params.get('min_samples_split', 2),
                            random_state=random_state
                        ),
                        'mlp_reg': MLPRegressor(
                            hidden_layer_sizes=(100, 50),
                            max_iter=1000,
                            random_state=random_state
                        )
                    }
                    
                    # Filter out None values
                    models = {k: v for k, v in models.items() if v is not None}

                    model = models.get(algorithm, models['rf_reg'])
                    
                    jobs[job_id]['progress'] = 50
                    
                    # Cross-validation if enabled
                    cv_scores = None
                    if enable_cv:
                        try:
                            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv_folds, scoring='neg_mean_squared_error', n_jobs=-1)
                            jobs[job_id]['cv_scores'] = (-cv_scores).tolist()  # Convert back to positive MSE
                        except Exception as e:
                            jobs[job_id]['cv_error'] = str(e)
                    
                    jobs[job_id]['progress'] = 60
                    
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    
                    jobs[job_id]['progress'] = 70
                    
                    # Calculate advanced metrics
                    metrics = calculate_advanced_metrics(y_test, y_pred, task, model, X_test_scaled)
                    
                    jobs[job_id]['progress'] = 75
                    
                jobs[job_id]['progress'] = 80
                
                # Calculate training time
                training_time = time.time() - start_time
                
                # Store model in registry
                model_registry[job_id] = {
                    'model': model,
                    'scaler': scaler,
                    'label_encoders': label_encoders if task in ['classification', 'neural_classification'] else {},
                    'target_encoder': target_encoder if task in ['classification', 'neural_classification'] else None,
                    'feature_names': X.columns.tolist(),
                    'trained_at': datetime.now().isoformat()
                }
                
                # Store comprehensive result
                jobs[job_id]['result'] = {
                    'metrics': metrics,
                    'feature_importance': feature_importance,
                    **predictions,
                    'algorithm': algorithm,
                    'task': task,
                    'target_column': target,
                    'automl_used': enable_automl,
                    'best_params': best_params if enable_automl else None,
                    'scaler_type': scaler_type,
                    'test_size': test_size,
                    'training_time_seconds': round(training_time, 2),
                    'n_samples_train': len(X_train),
                    'n_samples_test': len(X_test),
                    'n_features': X.shape[1],
                    'cv_scores': jobs.get(job_id, {}).get('cv_scores'),
                    'model_id': job_id
                }
                
            elif task == 'clustering':
                # Unsupervised clustering
                from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, SpectralClustering
                from sklearn.mixture import GaussianMixture
                from sklearn.preprocessing import StandardScaler
                
                X = df.select_dtypes(include=[np.number])
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                jobs[job_id]['progress'] = 50
                
                models = {
                    'kmeans': KMeans(n_clusters=5, random_state=random_state),
                    'dbscan': DBSCAN(eps=0.5, min_samples=5),
                    'hierarchical': AgglomerativeClustering(n_clusters=5),
                    'gaussian': GaussianMixture(n_components=5, random_state=random_state),
                    'spectral': SpectralClustering(n_clusters=5, random_state=random_state)
                }
                
                model = models.get(algorithm, models['kmeans'])
                labels = model.fit_predict(X_scaled)
                
                # Calculate silhouette score
                from sklearn.metrics import silhouette_score
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                
                metrics = {
                    'n_clusters': n_clusters,
                    'silhouette_score': silhouette_score(X_scaled, labels) if n_clusters > 1 else 0
                }
                
                jobs[job_id]['result'] = {
                    'metrics': metrics,
                    'algorithm': algorithm,
                    'task': task
                }
            
            elif task == 'dimensionality':
                # Dimensionality reduction
                from sklearn.decomposition import PCA, FastICA, NMF
                from sklearn.manifold import TSNE
                
                X = df.select_dtypes(include=[np.number])
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                jobs[job_id]['progress'] = 50
                
                models = {
                    'pca': PCA(n_components=2),
                    'tsne': TSNE(n_components=2, random_state=random_state),
                    'fast_ica': FastICA(n_components=2, random_state=random_state),
                    'nmf': NMF(n_components=2)
                }
                
                model = models.get(algorithm, models['pca'])
                X_reduced = model.fit_transform(X_scaled)
                
                metrics = {
                    'original_dims': X.shape[1],
                    'reduced_dims': 2,
                    'variance_explained': float(model.explained_variance_ratio_.sum()) if hasattr(model, 'explained_variance_ratio_') else 0
                }
                
                jobs[job_id]['result'] = {
                    'metrics': metrics,
                    'algorithm': algorithm,
                    'task': task
                }
            
            elif task == 'anomaly':
                # Anomaly detection
                from sklearn.ensemble import IsolationForest
                from sklearn.svm import OneClassSVM
                
                X = df.select_dtypes(include=[np.number])
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                jobs[job_id]['progress'] = 50
                
                models = {
                    'isolation_forest': IsolationForest(contamination=0.1, random_state=random_state),
                    'one_class_svm': OneClassSVM(kernel='rbf')
                }
                
                model = models.get(algorithm, models['isolation_forest'])
                predictions = model.fit_predict(X_scaled)
                
                n_anomalies = (predictions == -1).sum()
                
                metrics = {
                    'total_samples': len(X),
                    'anomalies_detected': int(n_anomalies),
                    'anomaly_percentage': float((n_anomalies / len(X)) * 100)
                }
                
                jobs[job_id]['result'] = {
                    'metrics': metrics,
                    'algorithm': algorithm,
                    'task': task
                }
            
            jobs[job_id]['progress'] = 100
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['duration'] = time.time() - start_time
            
        except Exception as e:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
    
    threading.Thread(target=run_training).start()
    return jsonify({'job_id': job_id})

@bp.route('/api/status/<job_id>', methods=['GET'])
def status(job_id):
    return jsonify(jobs.get(job_id, {}))

@bp.route('/api/shap/summary/<job_id>', methods=['GET'])
def shap_summary(job_id):
    """Generate SHAP summary plot for global feature importance"""
    job = jobs.get(job_id)
    if not job or job['status'] != 'completed':
        return jsonify({'error': 'Model not trained or job not found'}), 400
    
    try:
        import shap
        import matplotlib.pyplot as plt
        
        dataset_id = session.get('dataset_id')
        if not dataset_id:
            return jsonify({'error': 'No dataset loaded'}), 400
        
        df, _ = current_app.dataset_store.load(dataset_id)
        target = job['result'].get('target_column')
        
        if not target:
            return jsonify({'error': 'Target column not found'}), 400
        
        # Prepare data
        X = df.drop(columns=[target])
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Recreate model (simplified - in production would save/load model)
        algorithm = job['result']['algorithm']
        task = job['result']['task']
        
        if task in ['classification', 'neural_classification']:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            y = df[target]
            if y.dtype == 'object':
                le = LabelEncoder()
                y = le.fit_transform(y)
            model.fit(X_scaled, y)
        elif task in ['regression', 'neural_regression']:
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            y = df[target]
            model.fit(X_scaled, y)
        else:
            return jsonify({'error': 'SHAP only supported for supervised learning'}), 400
        
        # Generate SHAP values
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_scaled[:100])  # Sample for speed
        
        # Create summary plot
        if task in ['classification', 'neural_classification']:
            shap.summary_plot(shap_values[1], X.iloc[:100], show=False, plot_type="bar")
        else:
            shap.summary_plot(shap_values, X.iloc[:100], show=False, plot_type="bar")
        
        # Convert to Plotly
        fig = plt.gcf()
        import io
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        plt.close()
        
        # For now, return simple bar chart of feature importance
        feature_imp = job['result'].get('feature_importance', {})
        if feature_imp:
            features = list(feature_imp.keys())
            importances = list(feature_imp.values())
            
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Bar(
                x=importances,
                y=features,
                orientation='h',
                marker_color='rgb(99, 102, 241)'
            )])
            fig.update_layout(
                title='SHAP Feature Importance',
                xaxis_title='SHAP Value',
                yaxis_title='Feature',
                template='plotly_white',
                height=500
            )
            
            return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
        
        return jsonify({'error': 'No feature importance available'}), 400
        
    except Exception as e:
        return jsonify({'error': f'SHAP generation failed: {str(e)}'}), 400

@bp.route('/api/shap/dependence/<job_id>', methods=['GET'])
def shap_dependence(job_id):
    """Generate SHAP dependence plot for a specific feature"""
    job = jobs.get(job_id)
    if not job or job['status'] != 'completed':
        return jsonify({'error': 'Model not trained or job not found'}), 400
    
    feature = request.args.get('feature')
    if not feature:
        return jsonify({'error': 'No feature specified'}), 400
    
    try:
        import shap
        import matplotlib.pyplot as plt
        
        dataset_id = session.get('dataset_id')
        if not dataset_id:
            return jsonify({'error': 'No dataset loaded'}), 400
        
        df, _ = current_app.dataset_store.load(dataset_id)
        target = job['result'].get('target_column')
        
        if not target:
            return jsonify({'error': 'Target column not found'}), 400
        
        # Prepare data
        X = df.drop(columns=[target])
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Recreate model
        algorithm = job['result']['algorithm']
        task = job['result']['task']
        
        if task in ['classification', 'neural_classification']:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            y = df[target]
            if y.dtype == 'object':
                le = LabelEncoder()
                y = le.fit_transform(y)
            model.fit(X_scaled, y)
        elif task in ['regression', 'neural_regression']:
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            y = df[target]
            model.fit(X_scaled, y)
        else:
            return jsonify({'error': 'SHAP only supported for supervised learning'}), 400
        
        # Generate SHAP values
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_scaled[:200])
        
        # Create dependence plot
        feature_idx = list(X.columns).index(feature) if feature in X.columns else 0
        
        import plotly.graph_objects as go
        import numpy as np
        
        shap_vals = shap_values[1][:, feature_idx] if isinstance(shap_values, list) else shap_values[:, feature_idx]
        feature_vals = X[feature].iloc[:200]
        
        fig = go.Figure(data=go.Scatter(
            x=feature_vals,
            y=shap_vals,
            mode='markers',
            marker=dict(
                size=6,
                color=shap_vals,
                colorscale='RdBu',
                showscale=True,
                colorbar=dict(title='SHAP value')
            ),
            name=feature
        ))
        
        fig.update_layout(
            title=f'SHAP Dependence Plot: {feature}',
            xaxis_title=feature,
            yaxis_title='SHAP value',
            template='plotly_white',
            height=500
        )
        
        return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
        
    except Exception as e:
        return jsonify({'error': f'SHAP dependence plot failed: {str(e)}'}), 400

@bp.route('/api/models/list', methods=['GET'])
def list_models():
    """List all trained models in registry"""
    models_info = []
    for job_id, info in jobs.items():
        if info['status'] == 'completed' and info.get('result'):
            models_info.append({
                'model_id': job_id,
                'algorithm': info['result'].get('algorithm'),
                'task': info['result'].get('task'),
                'target_column': info['result'].get('target_column'),
                'trained_at': info.get('started_at'),
                'training_time': info['result'].get('training_time_seconds'),
                'metrics_summary': {k: v for k, v in info['result'].get('metrics', {}).items() 
                                   if isinstance(v, (int, float)) and not isinstance(v, bool)}
            })
    return jsonify({'models': models_info})

@bp.route('/api/models/compare', methods=['POST'])
def compare_models():
    """Compare multiple models side by side"""
    data = request.json
    model_ids = data.get('model_ids', [])
    
    if not model_ids:
        return jsonify({'error': 'No model IDs provided'}), 400
    
    comparison = []
    for model_id in model_ids:
        job = jobs.get(model_id)
        if job and job['status'] == 'completed' and job.get('result'):
            comparison.append({
                'model_id': model_id,
                'algorithm': job['result'].get('algorithm'),
                'task': job['result'].get('task'),
                'metrics': job['result'].get('metrics', {}),
                'cv_scores': job.get('cv_scores'),
                'training_time': job['result'].get('training_time_seconds'),
                'automl_used': job['result'].get('automl_used')
            })
    
    # Find best model based on primary metric
    if comparison:
        task_type = comparison[0]['task']
        if 'classification' in task_type:
            best_metric = 'f1_weighted'
        else:
            best_metric = 'r2'
        
        try:
            best_model = max(comparison, key=lambda x: x['metrics'].get(best_metric, 0))
            comparison.sort(key=lambda x: x['metrics'].get(best_metric, 0), reverse=True)
        except:
            best_model = None
        
        return jsonify({
            'comparison': comparison,
            'best_model': best_model['model_id'] if best_model else None,
            'best_metric': best_metric
        })
    
    return jsonify({'error': 'No valid models found'}), 404

@bp.route('/api/predict', methods=['POST'])
def predict():
    """Make predictions using a trained model"""
    data = request.json
    model_id = data.get('model_id')
    features = data.get('features')  # Dictionary of feature values
    
    if not model_id or not features:
        return jsonify({'error': 'Model ID and features required'}), 400
    
    # Get model from registry
    if model_id not in model_registry:
        return jsonify({'error': 'Model not found in registry'}), 404
    
    model_info = model_registry[model_id]
    model = model_info['model']
    scaler = model_info['scaler']
    feature_names = model_info['feature_names']
    
    try:
        # Create feature vector in correct order
        feature_vector = [features.get(col, 0) for col in feature_names]
        X = np.array(feature_vector).reshape(1, -1)
        
        # Scale features
        X_scaled = scaler.transform(X)
        
        # Make prediction
        prediction = model.predict(X_scaled)
        
        # Get probability if available (for classification)
        probabilities = None
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(X_scaled)
            probabilities = proba[0].tolist()
        
        return jsonify({
            'prediction': prediction[0],
            'probabilities': probabilities,
            'model_id': model_id,
            'algorithm': jobs[model_id]['result']['algorithm'] if model_id in jobs else None
        })
    
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@bp.route('/api/shap/waterfall/<job_id>', methods=['GET'])
def shap_waterfall(job_id):
    """Generate SHAP waterfall plot for individual prediction explanation"""
    job = jobs.get(job_id)
    if not job or job['status'] != 'completed':
        return jsonify({'error': 'Model not trained or job not found'}), 400
    
    sample_idx = request.args.get('sample', 0, type=int)
    
    try:
        import shap
        import plotly.graph_objects as go
        
        dataset_id = session.get('dataset_id')
        if not dataset_id:
            return jsonify({'error': 'No dataset loaded'}), 400
        
        df, _ = current_app.dataset_store.load(dataset_id)
        target = job['result'].get('target_column')
        
        if not target:
            return jsonify({'error': 'Target column not found'}), 400
        
        # Prepare data
        X = df.drop(columns=[target])
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Use stored model from registry if available
        if job_id in model_registry:
            model = model_registry[job_id]['model']
        else:
            # Recreate model
            algorithm = job['result']['algorithm']
            task = job['result']['task']
            
            if task in ['classification', 'neural_classification']:
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                y = df[target]
                if y.dtype == 'object':
                    le = LabelEncoder()
                    y = le.fit_transform(y)
                model.fit(X_scaled, y)
            elif task in ['regression', 'neural_regression']:
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                y = df[target]
                model.fit(X_scaled, y)
            else:
                return jsonify({'error': 'SHAP only supported for supervised learning'}), 400
        
        # Generate SHAP values
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_scaled[sample_idx:sample_idx+1])
        
        # Create waterfall visualization with Plotly
        feature_names = X.columns.tolist()
        
        if isinstance(shap_values, list):
            shap_vals = shap_values[1][0]  # For classification, use positive class
        else:
            shap_vals = shap_values[0]
        
        # Sort by absolute importance
        sorted_idx = np.argsort(np.abs(shap_vals))[::-1]
        top_features = sorted_idx[:10]  # Top 10 features
        
        fig = go.Figure()
        
        # Add bars
        for i, idx in enumerate(top_features):
            fig.add_trace(go.Bar(
                x=[shap_vals[idx]],
                y=[feature_names[idx]],
                orientation='h',
                name=feature_names[idx],
                marker_color='rgb(99, 102, 241)' if shap_vals[idx] >= 0 else 'rgb(239, 85, 59)'
            ))
        
        fig.update_layout(
            title=f'SHAP Waterfall Plot - Sample {sample_idx}',
            xaxis_title='SHAP Value',
            yaxis_title='Feature',
            template='plotly_white',
            height=500,
            showlegend=False
        )
        
        return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
    
    except Exception as e:
        return jsonify({'error': f'SHAP waterfall plot failed: {str(e)}'}), 400

@bp.route('/api/data-quality', methods=['POST'])
def assess_data_quality():
    """Comprehensive data quality assessment with a 0-100 quality score.

    Note: dataset is taken from the active session dataset_id.
    """
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400

    df, _ = current_app.dataset_store.load(dataset_id)
    if df is None or df.empty:
        return jsonify({'error': 'Dataset is empty'}), 400

    n_rows = len(df)
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / n_rows * 100).replace([np.inf, -np.inf], 0)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    # Duplicates
    exact_dup_rows = int(df.duplicated().sum())

    # Fuzzy duplicates (lightweight, sample)
    fuzzy_duplicates = []
    sample_df = df.head(min(500, n_rows)).copy()
    if categorical_cols:
        obj_cols_sample = [c for c in sample_df.columns if c in categorical_cols]
        for col in obj_cols_sample[:3]:
            vals = sample_df[col].dropna().astype(str).unique().tolist()[:80]
            for i in range(min(30, len(vals))):
                for j in range(i + 1, min(30, len(vals))):
                    a, b = vals[i], vals[j]
                    ratio = difflib.SequenceMatcher(None, a, b).ratio()
                    if ratio >= 0.92 and a != b:
                        fuzzy_duplicates.append({'column': col, 'a': a, 'b': b, 'similarity': ratio})
                        if len(fuzzy_duplicates) >= 10:
                            break
                if len(fuzzy_duplicates) >= 10:
                    break
            if len(fuzzy_duplicates) >= 10:
                break

    # Type validation suggestions
    type_issues = []
    type_corrections = []
    for col in categorical_cols[:200]:
        s = df[col]
        sample = s.dropna().astype(str).head(200)
        if len(sample) < 10:
            continue

        coerced = pd.to_numeric(sample, errors='coerce')
        success_rate = float((~coerced.isna()).sum() / len(sample) * 100)
        if success_rate >= 90:
            type_issues.append({'column': col, 'issue': 'Stored as categorical/text but values look numeric', 'success_rate_pct': success_rate})
            type_corrections.append({'column': col, 'suggested_action': 'Convert to numeric', 'method': 'pd.to_numeric(errors="coerce")'})

        parsed = pd.to_datetime(sample, errors='coerce', format='mixed')
        parsed_rate = float((~parsed.isna()).sum() / len(sample) * 100)
        if parsed_rate >= 80:
            type_issues.append({'column': col, 'issue': 'Stored as categorical/text but values look like dates', 'success_rate_pct': parsed_rate})
            type_corrections.append({'column': col, 'suggested_action': 'Convert to datetime', 'method': 'pd.to_datetime(errors="coerce", format="mixed")'})

    # Outlier detection (multimethod, sampled)
    outlier_report = {'columns': {}, 'flagged_columns': 0}
    outlier_df = df.sample(min(5000, n_rows), random_state=42) if n_rows > 5000 else df

    for col in numeric_cols:
        x = outlier_df[col].dropna().values.astype(float)
        if len(x) < 30:
            continue

        # Z-score
        z = np.abs(stats.zscore(x, nan_policy='omit')) if len(x) > 1 else np.zeros_like(x)
        z_flags = z > 3

        # IQR
        Q1 = np.nanpercentile(x, 25)
        Q3 = np.nanpercentile(x, 75)
        IQR = Q3 - Q1
        iqr_lower = Q1 - 1.5 * IQR
        iqr_upper = Q3 + 1.5 * IQR
        iqr_flags = (x < iqr_lower) | (x > iqr_upper)

        isof_flags = np.zeros_like(x, dtype=bool)
        lof_flags = np.zeros_like(x, dtype=bool)
        try:
            iso = IsolationForest(contamination=0.05, random_state=42)
            isof_flags = iso.fit_predict(x.reshape(-1, 1)) == -1

            lof = LocalOutlierFactor(n_neighbors=min(20, max(5, len(x)//20)), contamination=0.05)
            lof_flags = lof.fit_predict(x.reshape(-1, 1)) == -1
        except Exception:
            pass

        vote = z_flags.astype(int) + iqr_flags.astype(int) + isof_flags.astype(int) + lof_flags.astype(int)
        ensemble_flags = vote >= 3

        out_pct = float(ensemble_flags.mean() * 100) if len(ensemble_flags) else 0
        if out_pct > 0:
            outlier_report['columns'][col] = {
                'outlier_rate_pct': out_pct,
                'methods': {
                    'zscore>3': float(z_flags.mean() * 100),
                    'iqr_1_5x': float(iqr_flags.mean() * 100),
                    'isolation_forest': float(isof_flags.mean() * 100),
                    'lof': float(lof_flags.mean() * 100)
                }
            }
            outlier_report['flagged_columns'] += 1

    # Redundancy via correlation
    redundancy = {'redundant_pairs': [], 'redundant_columns': []}
    try:
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr(method='pearson').abs()
            threshold = 0.9
            redundant_cols = set()
            pairs = []
            for i, a in enumerate(corr.columns):
                for b in corr.columns[i+1:]:
                    val = corr.loc[a, b]
                    if pd.notna(val) and val >= threshold:
                        pairs.append({'a': a, 'b': b, 'abs_correlation': float(val)})
                        redundant_cols.add(a)
                        redundant_cols.add(b)
            redundancy['redundant_pairs'] = sorted(pairs, key=lambda x: x['abs_correlation'], reverse=True)[:20]
            redundancy['redundant_columns'] = sorted(list(redundant_cols))
    except Exception:
        pass

    # Categorical frequency analysis
    categorical_summary = {'columns': {}}
    for col in categorical_cols[:30]:
        freq = df[col].astype(str).value_counts(dropna=False)
        top = freq.head(10)
        low_freq = freq[freq / max(1, n_rows) < 0.01].head(10)
        categorical_summary['columns'][col] = {
            'top_categories': [{'value': str(k), 'count': int(v)} for k, v in top.items()],
            'low_frequency_warnings': [{'value': str(k), 'share_pct': float((v/n_rows)*100)} for k, v in low_freq.items()]
        }

    # Range validation suggestions
    range_validation = {}
    for col in numeric_cols:
        s = df[col]
        if s.dropna().shape[0] < 30:
            continue
        lo = float(s.quantile(0.01))
        hi = float(s.quantile(0.99))
        range_validation[col] = {'suggested_valid_min': lo, 'suggested_valid_max': hi, 'p01': lo, 'p99': hi}

    missingness_summary = {
        'columns_with_missing': int((missing_counts > 0).sum()),
        'max_missing_pct': float(missing_pct.max()) if len(missing_pct) else 0,
        'mean_missing_pct': float(missing_pct.mean()) if len(missing_pct) else 0
    }

    missing_suggestions = {}
    for col in missing_counts.index[missing_counts > 0].tolist():
        if col in numeric_cols:
            missing_suggestions[col] = {'impute_strategy_candidates': ['median', 'mean', 'knn(optional)'], 'recommended': 'median'}
        elif col in categorical_cols:
            missing_suggestions[col] = {'impute_strategy_candidates': ['mode', 'new_category(Unknown)'], 'recommended': 'mode'}
        else:
            missing_suggestions[col] = {'impute_strategy_candidates': ['unknown'], 'recommended': 'mode'}

    missing_penalty = min(40, missingness_summary['mean_missing_pct'] * 0.8)
    outlier_penalty = min(30, (sum(v['outlier_rate_pct'] for v in outlier_report['columns'].values()) / max(1, len(outlier_report['columns']))) if outlier_report['columns'] else 0)
    duplicate_penalty = min(20, (exact_dup_rows / max(1, n_rows)) * 100)
    type_penalty = min(15, len(type_corrections) * 5)
    redundancy_penalty = min(15, len(redundancy['redundant_columns']) * 2)

    raw_score = 100 - (missing_penalty + outlier_penalty + duplicate_penalty + type_penalty + redundancy_penalty)
    quality_score = int(max(0, min(100, raw_score)))

    return jsonify({
        'quality_score': quality_score,
        'score_breakdown': {
            'missing_penalty': float(missing_penalty),
            'outlier_penalty': float(outlier_penalty),
            'duplicate_penalty': float(duplicate_penalty),
            'type_penalty': float(type_penalty),
            'redundancy_penalty': float(redundancy_penalty)
        },
        'missingness_summary': missingness_summary,
        'missing_suggestions': missing_suggestions,
        'outliers': outlier_report,
        'type_issues': type_issues[:50],
        'type_corrections': type_corrections[:50],
        'duplicates': {
            'exact_duplicate_rows': exact_dup_rows,
            'fuzzy_duplicate_candidates': fuzzy_duplicates
        },
        'validity': {
            'range_validation': range_validation,
            'categorical_frequencies': categorical_summary
        },
        'redundancy': redundancy
    })

@bp.route('/api/feature/importance/permutation/<job_id>', methods=['GET'])
def permutation_importance(job_id):

    """Calculate permutation importance for features"""
    job = jobs.get(job_id)
    if not job or job['status'] != 'completed':
        return jsonify({'error': 'Model not trained or job not found'}), 400
    
    try:
        from sklearn.inspection import permutation_importance
        import plotly.graph_objects as go
        
        dataset_id = session.get('dataset_id')
        if not dataset_id:
            return jsonify({'error': 'No dataset loaded'}), 400
        
        df, _ = current_app.dataset_store.load(dataset_id)
        target = job['result'].get('target_column')
        
        if not target:
            return jsonify({'error': 'Target column not found'}), 400
        
        # Prepare data
        X = df.drop(columns=[target])
        y = df[target]
        
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        if job['result']['task'] in ['classification', 'neural_classification']:
            if y.dtype == 'object':
                le = LabelEncoder()
                y = le.fit_transform(y)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Use stored model
        if job_id in model_registry:
            model = model_registry[job_id]['model']
        else:
            return jsonify({'error': 'Model not in registry'}), 404
        
        # Calculate permutation importance
        perm_importance = permutation_importance(
            model, X_scaled, y, 
            n_repeats=10, 
            random_state=42,
            n_jobs=-1,
            scoring='f1_weighted' if 'classification' in job['result']['task'] else 'neg_mean_squared_error'
        )
        
        feature_names = X.columns.tolist()
        importances = perm_importance.importances_mean
        
        # Sort by importance
        sorted_idx = np.argsort(importances)[::-1]
        top_n = 15
        
        fig = go.Figure(data=[go.Bar(
            x=importances[sorted_idx[:top_n]],
            y=[feature_names[i] for i in sorted_idx[:top_n]],
            orientation='h',
            marker_color='rgb(99, 102, 241)'
        )])
        
        fig.update_layout(
            title='Permutation Feature Importance',
            xaxis_title='Importance (metric decrease when shuffled)',
            yaxis_title='Feature',
            template='plotly_white',
            height=500
        )
        
        return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
    
    except Exception as e:
        return jsonify({'error': f'Permutation importance failed: {str(e)}'}), 400

@bp.route('/api/learning_curve/<job_id>', methods=['GET'])
def learning_curve(job_id):
    """Generate learning curve to diagnose bias-variance tradeoff"""
    job = jobs.get(job_id)
    if not job or job['status'] != 'completed':
        return jsonify({'error': 'Model not trained or job not found'}), 400
    
    try:
        from sklearn.model_selection import learning_curve
        import plotly.graph_objects as go
        
        dataset_id = session.get('dataset_id')
        if not dataset_id:
            return jsonify({'error': 'No dataset loaded'}), 400
        
        df, _ = current_app.dataset_store.load(dataset_id)
        target = job['result'].get('target_column')
        
        if not target:
            return jsonify({'error': 'Target column not found'}), 400
        
        # Prepare data
        X = df.drop(columns=[target])
        y = df[target]
        
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        if job['result']['task'] in ['classification', 'neural_classification']:
            if y.dtype == 'object':
                le = LabelEncoder()
                y = le.fit_transform(y)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Use stored model
        if job_id in model_registry:
            model = model_registry[job_id]['model']
        else:
            return jsonify({'error': 'Model not in registry'}), 404
        
        # Calculate learning curve
        train_sizes, train_scores, val_scores = learning_curve(
            model, X_scaled, y,
            train_sizes=np.linspace(0.1, 1.0, 10),
            cv=5,
            scoring='f1_weighted' if 'classification' in job['result']['task'] else 'neg_mean_squared_error',
            n_jobs=-1
        )
        
        train_mean = train_scores.mean(axis=1)
        train_std = train_scores.std(axis=1)
        val_mean = val_scores.mean(axis=1)
        val_std = val_scores.std(axis=1)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=train_sizes,
            y=train_mean,
            mode='lines+markers',
            name='Training Score',
            line=dict(color='rgb(99, 102, 241)'),
            error_y=dict(type='data', array=train_std, visible=True)
        ))
        
        fig.add_trace(go.Scatter(
            x=train_sizes,
            y=val_mean,
            mode='lines+markers',
            name='Validation Score',
            line=dict(color='rgb(239, 85, 59)'),
            error_y=dict(type='data', array=val_std, visible=True)
        ))
        
        fig.update_layout(
            title='Learning Curve',
            xaxis_title='Training Set Size',
            yaxis_title='Score',
            template='plotly_white',
            height=500
        )
        
        return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
    
    except Exception as e:
        return jsonify({'error': f'Learning curve generation failed: {str(e)}'}), 400

@bp.route('/api/validation_curve/<job_id>', methods=['GET'])
def validation_curve(job_id):
    """Generate validation curve for hyperparameter tuning insights"""
    job = jobs.get(job_id)
    if not job or job['status'] != 'completed':
        return jsonify({'error': 'Model not trained or job not found'}), 400
    
    param_name = request.args.get('param', 'max_depth')
    
    try:
        from sklearn.model_selection import validation_curve
        import plotly.graph_objects as go
        
        dataset_id = session.get('dataset_id')
        if not dataset_id:
            return jsonify({'error': 'No dataset loaded'}), 400
        
        df, _ = current_app.dataset_store.load(dataset_id)
        target = job['result'].get('target_column')
        
        if not target:
            return jsonify({'error': 'Target column not found'}), 400
        
        # Prepare data
        X = df.drop(columns=[target])
        y = df[target]
        
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        if job['result']['task'] in ['classification', 'neural_classification']:
            if y.dtype == 'object':
                le = LabelEncoder()
                y = le.fit_transform(y)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Use stored model
        if job_id in model_registry:
            model = model_registry[job_id]['model']
        else:
            return jsonify({'error': 'Model not in registry'}), 404
        
        # Define parameter range based on param_name
        if param_name == 'max_depth':
            param_range = np.arange(1, 21)
        elif param_name == 'n_estimators':
            param_range = np.arange(10, 210, 20)
        else:
            param_range = np.linspace(0.01, 1.0, 10)
        
        # Calculate validation curve
        train_scores, val_scores = validation_curve(
            model, X_scaled, y,
            param_name=param_name,
            param_range=param_range,
            cv=5,
            scoring='f1_weighted' if 'classification' in job['result']['task'] else 'neg_mean_squared_error',
            n_jobs=-1
        )
        
        train_mean = train_scores.mean(axis=1)
        train_std = train_scores.std(axis=1)
        val_mean = val_scores.mean(axis=1)
        val_std = val_scores.std(axis=1)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=param_range,
            y=train_mean,
            mode='lines+markers',
            name='Training Score',
            line=dict(color='rgb(99, 102, 241)'),
            error_y=dict(type='data', array=train_std, visible=True)
        ))
        
        fig.add_trace(go.Scatter(
            x=param_range,
            y=val_mean,
            mode='lines+markers',
            name='Validation Score',
            line=dict(color='rgb(239, 85, 59)'),
            error_y=dict(type='data', array=val_std, visible=True)
        ))
        
        fig.update_layout(
            title=f'Validation Curve for {param_name}',
            xaxis_title=param_name,
            yaxis_title='Score',
            template='plotly_white',
            height=500
        )
        
        return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
    
    except Exception as e:
        return jsonify({'error': f'Validation curve generation failed: {str(e)}'}), 400
