from flask import Blueprint, render_template, session, jsonify, request, current_app
import uuid
import threading
import pandas as pd
import numpy as np
import logging
import time
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                            mean_squared_error, r2_score, mean_absolute_error, 
                            confusion_matrix, roc_auc_score,
                            explained_variance_score)
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    IsolationForest
)
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB

from sklearn.linear_model import LogisticRegression, LinearRegression, Lasso, Ridge, ElasticNet
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import (
    silhouette_score, calinski_harabasz_score, davies_bouldin_score
)

# Try to import MAPE from its new location in sklearn 1.4+
try:
    from sklearn.metrics import mean_absolute_percentage_error
except ImportError:
    # For older sklearn versions
    from sklearn.metrics._regression import mean_absolute_percentage_error

# Import MLOps components to enable model registration
from core.model_registry import register as register_model_in_registry
from core.experiment_tracker import log_experiment as log_exp_to_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('ml', __name__)
jobs = {}
model_registry = {}

# Constants
N_JOBS = -1  # Use all CPUs

# Try to import optional libraries
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    import lightgbm as lgb
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False


def get_numeric_columns(df):
    """Get numeric column names from DataFrame"""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def get_categorical_columns(df):
    """Get categorical column names from DataFrame"""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()


def get_datetime_columns(df):
    """Get datetime column names from DataFrame"""
    return df.select_dtypes(include=['datetime64']).columns.tolist()


def build_preprocessor(df, target_col, encoding_strategy='onehot'):
    """
    Build a ColumnTransformer preprocessor that handles numeric and categorical features separately.
    Based on the working implementation from make_a_model.py
    """
    X = df.drop(columns=[target_col])
    
    numeric_cols = get_numeric_columns(X)
    cat_cols = get_categorical_columns(X)
    
    transformers = []
    
    # Numeric transformer: impute + scale
    if numeric_cols:
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        transformers.append(('num', numeric_transformer, numeric_cols))
    
    # Categorical transformer: impute + encode
    if cat_cols:
        if encoding_strategy == 'onehot':
            cat_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
            ])
        else:
            cat_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))
            ])
        transformers.append(('cat', cat_transformer, cat_cols))
    
    if not transformers:
        raise ValueError("No valid features found")
    
    preprocessor = ColumnTransformer(transformers=transformers, remainder='drop')
    
    def get_feature_names_out(preproc):
        try:
            return preproc.get_feature_names_out().tolist()
        except:
            return [f"feature_{i}" for i in range(preproc.transform(X).shape[1])]
    
    return preprocessor, numeric_cols, cat_cols, get_feature_names_out


def model_key_to_estimator(model_key, problem_type='Classification'):
    """Map model key string to actual estimator instance."""
    model_map = {
        'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=N_JOBS),
        'RandomForestReg': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=N_JOBS),
        'ExtraTrees': ExtraTreesClassifier(n_estimators=100, random_state=42, n_jobs=N_JOBS),
        'ExtraTreesReg': ExtraTreesRegressor(n_estimators=100, random_state=42, n_jobs=N_JOBS),
        'GradientBoosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'GradientBoostingReg': GradientBoostingRegressor(n_estimators=100, random_state=42),
        'AdaBoost': AdaBoostClassifier(n_estimators=100, random_state=42),
        'AdaBoostReg': AdaBoostRegressor(n_estimators=100, random_state=42),
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
        'LinearRegression': LinearRegression(),
        'Ridge': Ridge(random_state=42),
        'Lasso': Lasso(random_state=42, max_iter=10000),
        'SVM': SVC(probability=True, random_state=42),
        'SVR': SVR(),
        'KNN': KNeighborsClassifier(n_jobs=N_JOBS),
        'KNNReg': KNeighborsRegressor(n_jobs=N_JOBS),
        'DecisionTree': DecisionTreeClassifier(random_state=42),
        'DecisionTreeReg': DecisionTreeRegressor(random_state=42),
        'NaiveBayes': GaussianNB() if 'GaussianNB' in globals() else RandomForestClassifier(random_state=42),
    }
    
    if XGB_AVAILABLE:
        if problem_type == 'Classification':
            model_map['XGBoost'] = xgb.XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss', n_jobs=N_JOBS)
        else:
            model_map['XGBoostReg'] = xgb.XGBRegressor(n_estimators=100, random_state=42, n_jobs=N_JOBS)
    
    if LGBM_AVAILABLE:
        if problem_type == 'Classification':
            model_map['LightGBM'] = lgb.LGBMClassifier(n_estimators=100, random_state=42, verbose=-1, n_jobs=N_JOBS)
        else:
            model_map['LightGBMReg'] = lgb.LGBMRegressor(n_estimators=100, random_state=42, verbose=-1, n_jobs=N_JOBS)
    
    if CATBOOST_AVAILABLE:
        if problem_type == 'Classification':
            model_map['CatBoost'] = CatBoostClassifier(iterations=100, random_state=42, verbose=0)
        else:
            model_map['CatBoostReg'] = CatBoostRegressor(iterations=100, random_state=42, verbose=0)
    
    if model_key not in model_map:
        logger.warning(f"Unknown model key: {model_key}, defaulting to Random Forest")
        return model_map['RandomForest'] if problem_type == 'Classification' else model_map['RandomForestReg']
    
    return model_map[model_key]


def calculate_metrics(y_true, y_pred, task, model=None, X_test=None):
    """Calculate evaluation metrics"""
    metrics = {}
    
    if task in ['classification', 'neural_classification']:
        metrics.update({
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision_weighted': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
            'recall_weighted': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
            'f1_weighted': float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
        })
        
        try:
            if hasattr(model, 'predict_proba'):
                y_prob = model.predict_proba(X_test)
                if y_prob.shape[1] == 2:
                    metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob[:, 1]))
        except Exception as e:
            logger.warning(f"ROC-AUC failed: {e}")
        
        try:
            cm = confusion_matrix(y_true, y_pred)
            metrics['confusion_matrix'] = cm.tolist()
        except:
            pass
    
    elif task in ['regression', 'neural_regression']:
        metrics.update({
            'mse': float(mean_squared_error(y_true, y_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'r2': float(r2_score(y_true, y_pred)),
        })
        
        try:
            metrics['mape'] = float(mean_absolute_percentage_error(y_true, y_pred))
        except:
            pass
    
    return metrics


@bp.route('/')
def ml_page():
    return render_template('ml.html', active_tab='ml')


@bp.route('/api/train', methods=['POST'])
def train():
    """Train ML model using Pipeline architecture with user-selected features"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    cfg = request.json
    target = cfg.get('target')
    features = cfg.get('features', [])  # List of selected feature columns
    task = cfg.get('task', 'classification')
    algorithm = cfg.get('algorithm', 'RandomForest')
    test_size = cfg.get('test_size', 0.2)
    enable_cv = cfg.get('cross_validation', True)
    cv_folds = cfg.get('cv_folds', 5)
    
    if not target:
        return jsonify({'error': 'No target column specified'}), 400
    
    # Load dataset in the main thread to avoid application context issues in the worker thread
    try:
        df, dataset_name = current_app.dataset_store.load(dataset_id)
        if df is None or df.empty:
            return jsonify({'error': 'Dataset is empty'}), 400
        if target not in df.columns:
            return jsonify({'error': f'Target "{target}" not found. Available: {", ".join(df.columns.tolist())}'}), 400
    except Exception as e:
        return jsonify({'error': f'Dataset loading failed: {str(e)}'}), 400
    
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
            logger.info(f"Job {job_id}: Starting training")
            
            # Use the dataset that was loaded in the main thread
            local_df = df.copy()  # Work with a copy to avoid any potential race conditions
            
            logger.info(f"Job {job_id}: Dataset loaded - {local_df.shape}")
            jobs[job_id]['progress'] = 10
            
            # Select features
            if features and len(features) > 0:
                # Use user-selected features
                invalid_features = [f for f in features if f not in local_df.columns]
                if invalid_features:
                    jobs[job_id]['status'] = 'failed'
                    jobs[job_id]['error'] = f'Invalid features: {", ".join(invalid_features)}'
                    return
                
                # Remove target from features if accidentally included
                features_local = [f for f in features if f != target]
                
                if len(features_local) == 0:
                    jobs[job_id]['status'] = 'failed'
                    jobs[job_id]['error'] = 'No valid feature columns selected'
                    return
                
                X = local_df[features_local]
                logger.info(f"Job {job_id}: Using {len(features_local)} selected features: {features_local}")
            else:
                # Use all columns except target
                X = local_df.drop(columns=[target])
                logger.info(f"Job {job_id}: Using all columns except target as features")
            
            y = local_df[target]
            
            # Encode categorical target
            target_encoder = None
            if task in ['classification', 'neural_classification']:
                if y.dtype == 'object' or y.dtype.name == 'category':
                    target_encoder = LabelEncoder()
                    y = target_encoder.fit_transform(y.astype(str))
            
            jobs[job_id]['progress'] = 20
            
            # Build preprocessor
            logger.info(f"Job {job_id}: Building preprocessor")
            temp_df = pd.concat([X, y.rename(target)], axis=1)
            preproc, numeric_cols, cat_cols, get_feature_names = build_preprocessor(temp_df, target)
            logger.info(f"Job {job_id}: Preprocessor - numeric: {len(numeric_cols)}, cat: {len(cat_cols)}")
            
            jobs[job_id]['progress'] = 30
            
            # Split data
            stratify_param = y if task in ['classification'] and len(np.unique(y)) > 1 else None
            
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42,
                    stratify=stratify_param
                )
            except Exception as e:
                logger.warning(f"Job {job_id}: Stratified split failed: {e}, using regular split")
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42
                )
            
            logger.info(f"Job {job_id}: Train: {X_train.shape}, Test: {X_test.shape}")
            jobs[job_id]['progress'] = 40
            
            # Create model and pipeline
            model = model_key_to_estimator(algorithm, task)
            pipe = Pipeline([('preproc', preproc), ('model', model)])
            
            jobs[job_id]['progress'] = 50
            
            # Cross-validation
            if enable_cv:
                try:
                    scoring = 'f1_weighted' if task in ['classification'] else 'r2'
                    cv = StratifiedKFold(cv_folds, shuffle=True, random_state=42) if stratify_param is not None else KFold(cv_folds, shuffle=True, random_state=42)
                    cv_scores = cross_val_score(pipe, X, y, cv=cv, scoring=scoring, n_jobs=N_JOBS)
                    jobs[job_id]['cv_scores'] = cv_scores.tolist()
                    logger.info(f"Job {job_id}: CV mean: {cv_scores.mean():.4f}")
                except Exception as e:
                    logger.warning(f"CV failed: {e}")
            
            jobs[job_id]['progress'] = 60
            
            # Train
            logger.info(f"Job {job_id}: Training...")
            pipe.fit(X_train, y_train)
            logger.info(f"Job {job_id}: Trained successfully")
            
            jobs[job_id]['progress'] = 70
            
            # Predict
            y_pred = pipe.predict(X_test)
            trained_model = pipe.named_steps['model']
            
            jobs[job_id]['progress'] = 80
            
            # Metrics
            metrics = calculate_metrics(y_test, y_pred, task, trained_model, X_test)
            
            jobs[job_id]['progress'] = 85
            
            # Feature importance
            feature_importance = {}
            try:
                if hasattr(trained_model, 'feature_importances_'):
                    preproc_fitted = pipe.named_steps['preproc']
                    feature_names = get_feature_names(preproc_fitted)
                    importances = trained_model.feature_importances_
                    
                    if len(feature_names) == len(importances):
                        feature_importance = {
                            name: float(imp) 
                            for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:20]
                        }
            except Exception as e:
                logger.warning(f"Feature importance failed: {e}")
            
            jobs[job_id]['progress'] = 90
            
            # Store model
            model_registry[job_id] = {
                'pipeline': pipe,
                'target_encoder': target_encoder,
                'feature_columns': features if features else X.columns.tolist(),
                'trained_at': datetime.now().isoformat(),
                'algorithm': algorithm,
                'task': task
            }
            
            training_time = time.time() - start_time
            
            # Prepare result data
            result_data = {
                'metrics': metrics,
                'feature_importance': feature_importance,
                'algorithm': algorithm,
                'task': task,
                'target_column': target,
                'feature_columns': features if features else X.columns.tolist(),
                'training_time_seconds': round(training_time, 2),
                'n_samples_train': len(X_train),
                'n_samples_test': len(X_test),
                'n_features': X.shape[1],
                'cv_scores': jobs.get(job_id, {}).get('cv_scores'),
                'model_id': job_id
            }
            
            # Register model in MLOps system
            try:
                model_id = register_model_in_registry(
                    name=f"{algorithm}_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    model_type=f"{algorithm} ({task})",
                    metrics=metrics,
                    hyperparams={
                        'algorithm': algorithm,
                        'task': task,
                        'test_size': test_size,
                        'enable_cv': enable_cv,
                        'cv_folds': cv_folds if enable_cv else None,
                        'n_samples': len(X),
                        'n_features': X.shape[1],
                        'target_column': target
                    },
                    version="1.0"
                )
                
                # Log experiment to MLOps system
                log_exp_to_db(
                    name=f"Training_{algorithm}_{target}",
                    params={
                        'algorithm': algorithm,
                        'task': task,
                        'test_size': test_size,
                        'enable_cv': enable_cv,
                        'cv_folds': cv_folds if enable_cv else None,
                        'n_samples': len(X),
                        'n_features': X.shape[1],
                        'target_column': target
                    },
                    metrics=metrics,
                    status='completed'
                )
                
                # Add model registry ID to result data
                result_data['mlops_model_id'] = model_id
            except Exception as e:
                logger.warning(f"Failed to register model in MLOps system: {e}")
            
            # Assign the complete result data
            jobs[job_id]['result'] = result_data
            
            jobs[job_id]['progress'] = 100
            jobs[job_id]['status'] = 'completed'
            
            logger.info(f"Job {job_id}: Completed in {training_time:.2f}s")
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = f'{str(e)}\n\n{error_traceback}'
            logger.error(f"Job {job_id}: Failed: {e}", exc_info=True)
    
    threading.Thread(target=run_training).start()
    return jsonify({'job_id': job_id})


@bp.route('/api/status/<job_id>', methods=['GET'])
def status(job_id):
    return jsonify(jobs.get(job_id, {'error': 'Job not found'}))


@bp.route('/api/models/list', methods=['GET'])
def list_models():
    models_info = []
    for job_id, info in jobs.items():
        if info['status'] == 'completed' and info.get('result'):
            models_info.append({
                'model_id': job_id,
                'algorithm': info['result'].get('algorithm'),
                'task': info['result'].get('task'),
                'trained_at': info.get('started_at'),
            })
    return jsonify({'models': models_info})


@bp.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        model_id = data.get('model_id')
        features = data.get('features')
        
        if not model_id or not features:
            return jsonify({'error': 'Model ID and features required'}), 400
        
        if model_id not in model_registry:
            return jsonify({'error': 'Model not found'}), 404
        
        model_info = model_registry[model_id]
        pipe = model_info['pipeline']
        target_encoder = model_info.get('target_encoder')
        
        feature_df = pd.DataFrame([features])
        prediction = pipe.predict(feature_df)[0]
        
        if target_encoder is not None:
            try:
                prediction = target_encoder.inverse_transform([prediction])[0]
            except:
                pass
        
        return jsonify({'prediction': prediction, 'model_id': model_id})
    
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@bp.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check system state"""
    dataset_id = session.get('dataset_id')
    
    debug_data = {
        'session_dataset_id': dataset_id,
        'ml_job_id': session.get('ml_job_id'),
        'active_jobs_count': len(jobs),
        'jobs_status': {k: v['status'] for k, v in jobs.items()},
        'model_registry_count': len(model_registry),
    }
    
    if dataset_id:
        try:
            df, name = current_app.dataset_store.load(dataset_id)
            if df is not None:
                debug_data['dataset_loaded'] = True
                debug_data['dataset_name'] = name
                debug_data['dataset_shape'] = list(df.shape)
                debug_data['dataset_columns'] = list(df.columns)
            else:
                debug_data['dataset_loaded'] = False
                debug_data['dataset_error'] = 'Dataset file not found'
        except Exception as e:
            debug_data['dataset_loaded'] = False
            debug_data['dataset_error'] = str(e)
    else:
        debug_data['dataset_loaded'] = False
        debug_data['dataset_error'] = 'No dataset_id in session'
    
    return jsonify(debug_data)


@bp.route('/api/unsupervised', methods=['POST'])
def unsupervised_learning():
    """Perform unsupervised learning (clustering, dimensionality reduction)"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    cfg = request.json
    
    task = cfg.get('task', 'clustering')  # clustering or dimensionality_reduction
    features = cfg.get('features', [])
    
    if not features:
        return jsonify({'error': 'No features selected'}), 400
    
    try:
        X = df[features]
        
        # Preprocess
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Store model in session
        job_id = str(uuid.uuid4())[:8]
        session['unsupervised_model'] = {
            'job_id': job_id,
            'model': model,
            'scaler': scaler,
            'features': features,
            'task': task,
            'timestamp': datetime.now().isoformat()
        }
        
        # Prepare result data
        result_data = {
            'success': True, 
            'task': task
        }
        
        # Update result_data with method-specific results
        if task == 'clustering':
            method = cfg.get('method', 'kmeans')
            n_clusters = cfg.get('n_clusters', 3)
            
            if method == 'kmeans':
                labels = model.labels_ if hasattr(model, 'labels_') else model.fit_predict(X_scaled)
                
                # Calculate silhouette score
                if n_clusters > 1 and n_clusters < len(X):
                    try:
                        sil_score = silhouette_score(X_scaled, labels)
                        result_data['silhouette_score'] = float(sil_score)
                    except:
                        pass
                
                result_data['labels'] = labels.tolist()
                result_data['n_clusters'] = n_clusters
                result_data['cluster_sizes'] = [int(np.sum(labels == i)) for i in range(n_clusters)]
                
            elif method == 'dbscan':
                labels = model.labels_
                
                result_data['labels'] = labels.tolist()
                result_data['n_clusters'] = len(set(labels)) - (1 if -1 in labels else 0)
                result_data['noise_points'] = int(np.sum(labels == -1))
            
            # Add cluster labels to dataframe for visualization
            df_result = df.copy()
            df_result['cluster'] = labels
            
            # Create visualization data (first 2 PCA components)
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            result_data['pca_x'] = X_pca[:, 0].tolist()
            result_data['pca_y'] = X_pca[:, 1].tolist()
            result_data['explained_variance'] = pca.explained_variance_ratio_.tolist()
            
        elif task == 'dimensionality_reduction':
            method = cfg.get('method', 'pca')
            n_components = cfg.get('n_components', 2)
            
            if method == 'pca':
                model = PCA(n_components=n_components)
                X_reduced = model.fit_transform(X_scaled)
                
                result_data['components'] = X_reduced.tolist()
                result_data['explained_variance'] = model.explained_variance_ratio_.tolist()
                result_data['n_components'] = n_components
                
            elif method == 'tsne':
                perplexity = min(cfg.get('perplexity', 30), len(X) - 1)
                model = TSNE(n_components=2, perplexity=perplexity, random_state=42)
                X_reduced = model.fit_transform(X_scaled)
                
                result_data['components'] = X_reduced.tolist()
                result_data['n_components'] = 2
        
        # Register unsupervised model in MLOps system
        try:
            model_id = register_model_in_registry(
                name=f"{cfg.get('method', 'Unsupervised')}_{task}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_type=f"{cfg.get('method', 'Unsupervised')} ({task})",
                metrics={},
                hyperparams={
                    'method': cfg.get('method', 'kmeans'),
                    'task': task,
                    'features': features,
                    'n_samples': len(X)
                },
                version="1.0"
            )
            
            # Log experiment to MLOps system
            log_exp_to_db(
                name=f"Unsupervised_{cfg.get('method', 'kmeans')}_{task}",
                params={
                    'method': cfg.get('method', 'kmeans'),
                    'task': task,
                    'features': features,
                    'n_samples': len(X)
                },
                metrics={},
                status='completed'
            )
            
            result_data['mlops_model_id'] = model_id
        except Exception as e:
            logger.warning(f"Failed to register unsupervised model in MLOps system: {e}")
        
        result_data['job_id'] = job_id
        return jsonify(result_data)
        
    except Exception as e:
        logger.error(f"Unsupervised learning error: {e}")
        return jsonify({'error': f'Failed: {str(e)}'}), 500


@bp.route('/api/export/code', methods=['POST'])
def export_training_code():
    """Export complete ML training pipeline as Python code"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, name = current_app.dataset_store.load(dataset_id)
    cfg = request.json
    
    target_col = cfg.get('target_col')
    problem_type = cfg.get('problem_type', 'classification')
    model_name = cfg.get('model_name', 'RandomForest')
    features = cfg.get('features', [])
    encoding = cfg.get('encoding', 'onehot')
    scaling = cfg.get('scaling', 'standard')
    
    if not target_col:
        return jsonify({'error': 'Target column required'}), 400
    
    # Generate comprehensive Python code
    code = f'''# Auto-generated Machine Learning Pipeline by FINESE2
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Dataset: {name}
# Problem Type: {problem_type}
# Target: {target_col}

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer
'''
    
    # Add model-specific imports
    if problem_type == 'classification':
        if model_name == 'RandomForest':
            code += 'from sklearn.ensemble import RandomForestClassifier\n'
        elif model_name == 'XGBoost':
            code += 'from xgboost import XGBClassifier\n'
        elif model_name == 'LightGBM':
            code += 'from lightgbm import LGBMClassifier\n'
        else:
            code += 'from sklearn.ensemble import RandomForestClassifier\n'
    else:
        if model_name == 'RandomForest':
            code += 'from sklearn.ensemble import RandomForestRegressor\n'
        elif model_name == 'XGBoost':
            code += 'from xgboost import XGBRegressor\n'
        elif model_name == 'LightGBM':
            code += 'from lightgbm import LGBMRegressor\n'
        else:
            code += 'from sklearn.ensemble import RandomForestRegressor\n'
    
    code += f'''
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib

# Load dataset
df = pd.read_csv("your_dataset.csv")

# Define features and target
target = "{target_col}"
features = {features if features else "[col for col in df.columns if col != target]"}

X = df[features]
y = df[target]

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique()) <= 10 else None)

# Identify numeric and categorical columns
numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

# Build preprocessor
numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", {"OneHotEncoder(handle_unknown='ignore', sparse_output=False)" if encoding == "onehot" else "OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)"})
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_cols),
        ("cat", categorical_transformer, categorical_cols)
    ]
)

# Build full pipeline
pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", {"RandomForestClassifier(random_state=42, n_jobs=-1)" if model_name == "RandomForest" and problem_type == "classification" else 
                   "RandomForestRegressor(random_state=42, n_jobs=-1)" if model_name == "RandomForest" else
                   "XGBClassifier(random_state=42)" if model_name == "XGBoost" and problem_type == "classification" else
                   "XGBRegressor(random_state=42)" if model_name == "XGBoost" else
                   "LGBMClassifier(random_state=42)" if model_name == "LightGBM" and problem_type == "classification" else
                   "LGBMRegressor(random_state=42)"})
])

# Train model
print("Training model...")
pipeline.fit(X_train, y_train)

# Evaluate
y_pred = pipeline.predict(X_test)

if "{problem_type}" == "classification":
    print(f"Accuracy: {{accuracy_score(y_test, y_pred):.4f}}")
    print(f"F1 Score: {{f1_score(y_test, y_pred, average='weighted'):.4f}}")
    print(f"\\nConfusion Matrix:\\n{{confusion_matrix(y_test, y_pred)}}")
else:
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    print(f"R² Score: {{r2_score(y_test, y_pred):.4f}}")
    print(f"RMSE: {{np.sqrt(mean_squared_error(y_test, y_pred)):.4f}}")
    print(f"MAE: {{mean_absolute_error(y_test, y_pred):.4f}}")

# Save model
joblib.dump(pipeline, "trained_model.pkl")
print("\\nModel saved as 'trained_model.pkl'")
'''
    
    return jsonify({
        'success': True,
        'code': code,
        'filename': f'finese2_{model_name.lower()}_{datetime.now().strftime("%Y%m%d_%H%M")}.py'
    })


@bp.route('/api/export/model/<model_id>', methods=['GET'])
def export_model(model_id):
    """Export a trained model as joblib file"""
    try:
        if model_id not in model_registry:
            return jsonify({'error': 'Model not found'}), 404
        
        import io
        from flask import send_file
        
        model_info = model_registry[model_id]
        pipeline = model_info['pipeline']
        
        # Create in-memory file
        buffer = io.BytesIO()
        joblib.dump(pipeline, buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=f'model_{model_id}.joblib'
        )
        
    except Exception as e:
        logger.error(f"Model export failed: {e}")
        return jsonify({'error': f'Model export failed: {str(e)}'}), 500


@bp.route('/api/export/model', methods=['POST'])
def export_model_post():
    """Export the most recently trained model as joblib file"""
    try:
        # Get the most recently trained model
        latest_job_id = None
        latest_time = None
        
        for job_id, info in jobs.items():
            if info['status'] == 'completed' and info.get('result'):
                # Extract the started_at time if available
                started_at_str = info.get('started_at')
                if started_at_str:
                    started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00') if started_at_str.endswith('Z') else started_at_str)
                    if not latest_time or started_at > latest_time:
                        latest_time = started_at
                        latest_job_id = job_id
        
        if not latest_job_id:
            return jsonify({'error': 'No trained models available'}), 404
        
        return export_model(latest_job_id)
        
    except Exception as e:
        logger.error(f"Model export failed: {e}")
        return jsonify({'error': f'Model export failed: {str(e)}'}), 500


@bp.route('/api/automl', methods=['POST'])
def automl():
    """Run automated machine learning to compare multiple models"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    cfg = request.json
    target = cfg.get('target')
    features = cfg.get('features', [])
    n_trials = cfg.get('n_trials', 50)
    
    if not target:
        return jsonify({'error': 'No target column specified'}), 400
    
    try:
        df, _ = current_app.dataset_store.load(dataset_id)
        
        if target not in df.columns:
            return jsonify({'error': f'Target "{target}" not found'}), 400
        
        # Select features
        if features and len(features) > 0:
            invalid_features = [f for f in features if f not in df.columns]
            if invalid_features:
                return jsonify({'error': f'Invalid features: {", ".join(invalid_features)}'}), 400
            features = [f for f in features if f != target]
            X = df[features]
        else:
            X = df.drop(columns=[target])
        
        y = df[target]
        
        # Determine task type
        if y.dtype == 'object' or y.dtype.name == 'category' or len(y.unique()) <= 20:
            task = 'classification'
        else:
            task = 'regression'
        
        # Prepare preprocessor
        temp_df = pd.concat([X, y.rename(target)], axis=1)
        preproc, _, _, get_feature_names = build_preprocessor(temp_df, target)
        
        # Define models to test based on task type
        if task == 'classification':
            models_to_test = [
                ('Random Forest', 'RandomForest'),
                ('Gradient Boosting', 'GradientBoosting'),
                ('XGBoost', 'XGBoost'),
                ('Logistic Regression', 'LogisticRegression'),
                ('SVM', 'SVM'),
                ('KNN', 'KNN'),
                ('Decision Tree', 'DecisionTree'),
            ]
        else:
            models_to_test = [
                ('Random Forest', 'RandomForestReg'),
                ('Gradient Boosting', 'GradientBoostingReg'),
                ('XGBoost', 'XGBoostReg'),
                ('Linear Regression', 'LinearRegression'),
                ('Ridge', 'Ridge'),
                ('SVR', 'SVR'),
                ('KNN Regressor', 'KNNReg'),
                ('Decision Tree Regressor', 'DecisionTreeReg'),
            ]
        
        # Filter out models that aren't available
        available_models = []
        for name, key in models_to_test:
            try:
                model = model_key_to_estimator(key, task)
                available_models.append((name, key))
            except:
                continue  # Skip unavailable models
        
        results = []
        for model_name, model_key in available_models:
            try:
                model = model_key_to_estimator(model_key, task)
                pipe = Pipeline([('preproc', preproc), ('model', model)])
                
                # Cross-validation
                if task == 'classification':
                    scoring = 'f1_weighted' if len(y.unique()) > 2 else 'f1'
                    cv = StratifiedKFold(5, shuffle=True, random_state=42)
                else:
                    scoring = 'r2'
                    cv = KFold(5, shuffle=True, random_state=42)
                
                cv_scores = cross_val_score(pipe, X, y, cv=cv, scoring=scoring, n_jobs=N_JOBS)
                
                results.append({
                    'name': model_name,
                    'algorithm': model_key,
                    'mean_cv_score': float(cv_scores.mean()),
                    'std_cv_score': float(cv_scores.std()),
                    'metrics': {
                        'cv_mean': float(cv_scores.mean()),
                        'cv_std': float(cv_scores.std())
                    }
                })
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                continue
        
        # Sort results by CV score
        results.sort(key=lambda x: x['mean_cv_score'], reverse=True)
        
        return jsonify({'results': results})
        
    except Exception as e:
        logger.error(f"AutoML failed: {e}")
        return jsonify({'error': f'AutoML failed: {str(e)}'}), 500