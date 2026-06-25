from flask import Blueprint, render_template, session, jsonify, request, current_app
import uuid
import threading
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import json

bp = Blueprint('ml', __name__)
jobs = {}

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
    
    if not target:
        return jsonify({'error': 'No target column specified'}), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'running', 'progress': 0, 'result': None}
    session['ml_job_id'] = job_id
    
    def run_training():
        try:
            df, _ = current_app.dataset_store.load(dataset_id)
            
            # Update progress
            jobs[job_id]['progress'] = 10
            
            # Prepare data
            if task in ['classification', 'regression', 'neural_classification', 'neural_regression']:
                # Supervised learning
                X = df.drop(columns=[target])
                y = df[target]
                
                # Handle categorical features
                categorical_cols = X.select_dtypes(include=['object']).columns
                for col in categorical_cols:
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
                
                # Handle categorical target for classification
                if task in ['classification', 'neural_classification']:
                    if y.dtype == 'object':
                        le = LabelEncoder()
                        y = le.fit_transform(y)
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=random_state
                )
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                jobs[job_id]['progress'] = 30
                
                # Train model based on algorithm
                metrics = {}
                feature_importance = {}
                predictions = {}
                
                if task in ['classification', 'neural_classification']:
                    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
                    from sklearn.linear_model import LogisticRegression
                    from sklearn.svm import SVC
                    from sklearn.neighbors import KNeighborsClassifier
                    from sklearn.tree import DecisionTreeClassifier
                    from sklearn.naive_bayes import GaussianNB
                    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
                    from sklearn.neural_network import MLPClassifier
                    
                    models = {
                        'rf': RandomForestClassifier(n_estimators=100, random_state=random_state),
                        'gb': GradientBoostingClassifier(n_estimators=100, random_state=random_state),
                        'lr': LogisticRegression(max_iter=1000, random_state=random_state),
                        'svm': SVC(kernel='rbf', random_state=random_state),
                        'knn': KNeighborsClassifier(n_neighbors=5),
                        'dt': DecisionTreeClassifier(random_state=random_state),
                        'nb': GaussianNB(),
                        'ada': AdaBoostClassifier(n_estimators=100, random_state=random_state),
                        'lda': LinearDiscriminantAnalysis(),
                        'qda': QuadraticDiscriminantAnalysis(),
                        'mlp_class': MLPClassifier(max_iter=1000, random_state=random_state)
                    }
                    
                    model = models.get(algorithm, models['rf'])
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    metrics = {
                        'accuracy': accuracy_score(y_test, y_pred),
                        'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                        'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
                        'f1_score': f1_score(y_test, y_pred, average='weighted', zero_division=0)
                    }
                    
                    # Feature importance
                    if hasattr(model, 'feature_importances_'):
                        feature_names = X.columns.tolist()
                        importances = model.feature_importances_.tolist()
                        feature_importance = dict(zip(feature_names, importances))
                        # Sort and take top 15
                        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:15])
                    
                    # Confusion matrix for binary/multiclass
                    from sklearn.metrics import confusion_matrix
                    cm = confusion_matrix(y_test, y_pred)
                    predictions = {
                        'confusion_matrix': {
                            'values': cm.tolist(),
                            'labels': list(set(y.tolist()))
                        }
                    }
                
                elif task in ['regression', 'neural_regression']:
                    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
                    from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
                    from sklearn.svm import SVR
                    from sklearn.neighbors import KNeighborsRegressor
                    from sklearn.tree import DecisionTreeRegressor
                    from sklearn.neural_network import MLPRegressor
                    
                    models = {
                        'rf_reg': RandomForestRegressor(n_estimators=100, random_state=random_state),
                        'gb_reg': GradientBoostingRegressor(n_estimators=100, random_state=random_state),
                        'lr_reg': LinearRegression(),
                        'ridge': Ridge(alpha=1.0),
                        'lasso': Lasso(alpha=1.0),
                        'svr': SVR(kernel='rbf'),
                        'knn_reg': KNeighborsRegressor(n_neighbors=5),
                        'dt_reg': DecisionTreeRegressor(random_state=random_state),
                        'elastic': ElasticNet(alpha=1.0, l1_ratio=0.5),
                        'mlp_reg': MLPRegressor(max_iter=1000, random_state=random_state)
                    }
                    
                    model = models.get(algorithm, models['rf_reg'])
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    metrics = {
                        'mse': mean_squared_error(y_test, y_pred),
                        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                        'mae': np.mean(np.abs(y_test - y_pred)),
                        'r2': r2_score(y_test, y_pred)
                    }
                    
                    # Feature importance
                    if hasattr(model, 'feature_importances_'):
                        feature_names = X.columns.tolist()
                        importances = model.feature_importances_.tolist()
                        feature_importance = dict(zip(feature_names, importances))
                        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:15])
                    
                    # Residuals plot
                    predictions = {
                        'residuals': {
                            'predicted': y_pred[:100].tolist(),
                            'actual': y_test[:100].tolist()
                        }
                    }
                
                jobs[job_id]['progress'] = 80
                
                # Store result
                jobs[job_id]['result'] = {
                    'metrics': metrics,
                    'feature_importance': feature_importance,
                    **predictions,
                    'algorithm': algorithm,
                    'task': task
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
            
        except Exception as e:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
    
    threading.Thread(target=run_training).start()
    return jsonify({'job_id': job_id})

@bp.route('/api/status/<job_id>', methods=['GET'])
def status(job_id):
    return jsonify(jobs.get(job_id, {}))
