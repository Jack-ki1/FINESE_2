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

def optimize_with_optuna(X_train, y_train, task, algorithm, n_trials=20):
    """Use Optuna for hyperparameter optimization"""
    try:
        import optuna
        
        def objective(trial):
            if task == 'classification':
                if algorithm == 'rf':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                        'max_depth': trial.suggest_int('max_depth', 3, 20),
                        'min_samples_split': trial.suggest_int('min_samples_split', 2, 20)
                    }
                    from sklearn.ensemble import RandomForestClassifier
                    model = RandomForestClassifier(**params, random_state=42)
                elif algorithm == 'gb':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                        'max_depth': trial.suggest_int('max_depth', 3, 10)
                    }
                    from sklearn.ensemble import GradientBoostingClassifier
                    model = GradientBoostingClassifier(**params, random_state=42)
                else:
                    from sklearn.ensemble import RandomForestClassifier
                    model = RandomForestClassifier(random_state=42)
                
                X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                return accuracy_score(y_val, y_pred)
            
            elif task == 'regression':
                if algorithm == 'rf_reg':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                        'max_depth': trial.suggest_int('max_depth', 3, 20)
                    }
                    from sklearn.ensemble import RandomForestRegressor
                    model = RandomForestRegressor(**params, random_state=42)
                else:
                    from sklearn.ensemble import RandomForestRegressor
                    model = RandomForestRegressor(random_state=42)
                
                X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                return -mean_squared_error(y_val, y_pred)  # Negative for minimization
            
            return 0
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        return study.best_params, study.best_value
        
    except ImportError:
        return {}, 0

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
    n_trials = cfg.get('n_trials', 20)
    
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
                
                # AutoML optimization if enabled
                best_params = {}
                if enable_automl:
                    jobs[job_id]['progress'] = 35
                    best_params, best_score = optimize_with_optuna(
                        X_train_scaled, y_train, task, algorithm, n_trials
                    )
                    jobs[job_id]['progress'] = 45
                
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
                        'rf': RandomForestClassifier(n_estimators=best_params.get('n_estimators', 100), 
                                                    max_depth=best_params.get('max_depth', None),
                                                    min_samples_split=best_params.get('min_samples_split', 2),
                                                    random_state=random_state),
                        'gb': GradientBoostingClassifier(n_estimators=best_params.get('n_estimators', 100),
                                                        learning_rate=best_params.get('learning_rate', 0.1),
                                                        max_depth=best_params.get('max_depth', 3),
                                                        random_state=random_state),
                        'lr': LogisticRegression(max_iter=1000, random_state=random_state),
                        'svm': SVC(kernel='rbf', random_state=random_state),
                        'knn': KNeighborsClassifier(n_neighbors=5),
                        'dt': DecisionTreeClassifier(max_depth=best_params.get('max_depth', None), random_state=random_state),
                        'nb': GaussianNB(),
                        'ada': AdaBoostClassifier(n_estimators=best_params.get('n_estimators', 100), random_state=random_state),
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
                        'rf_reg': RandomForestRegressor(n_estimators=best_params.get('n_estimators', 100),
                                                       max_depth=best_params.get('max_depth', None),
                                                       random_state=random_state),
                        'gb_reg': GradientBoostingRegressor(n_estimators=best_params.get('n_estimators', 100),
                                                           learning_rate=best_params.get('learning_rate', 0.1),
                                                           max_depth=best_params.get('max_depth', 3),
                                                           random_state=random_state),
                        'lr_reg': LinearRegression(),
                        'ridge': Ridge(alpha=best_params.get('alpha', 1.0)),
                        'lasso': Lasso(alpha=best_params.get('alpha', 1.0)),
                        'svr': SVR(kernel='rbf'),
                        'knn_reg': KNeighborsRegressor(n_neighbors=5),
                        'dt_reg': DecisionTreeRegressor(max_depth=best_params.get('max_depth', None), random_state=random_state),
                        'elastic': ElasticNet(alpha=best_params.get('alpha', 1.0), l1_ratio=0.5),
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
                    'task': task,
                    'target_column': target,
                    'automl_used': enable_automl,
                    'best_params': best_params if enable_automl else None
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
