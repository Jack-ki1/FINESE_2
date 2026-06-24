"""
FINESE2 - Consolidated MLOps Module
Comprehensive model lifecycle management and experiment tracking
"""
import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import hashlib
import logging
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
import pickle

logger = logging.getLogger(__name__)


class MLOpsManager:
    """
    Consolidated MLOps manager for model lifecycle, experiment tracking, and model registry
    """
    
    def __init__(self):
        self.experiments_dir = Path("experiments")
        self.models_dir = Path("models")
        self.experiments_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.current_experiment_id = None
        self.experiment_data = {}
    
    def start_experiment(self, experiment_name: str, description: str = "") -> str:
        """Start a new experiment and return experiment ID"""
        experiment_id = hashlib.md5(f"{experiment_name}_{datetime.now()}".encode()).hexdigest()[:12]
        
        self.current_experiment_id = experiment_id
        self.experiment_data = {
            'id': experiment_id,
            'name': experiment_name,
            'description': description,
            'start_time': datetime.now().isoformat(),
            'metrics': {},
            'parameters': {},
            'artifacts': [],
            'tags': []
        }
        
        # Create experiment directory
        exp_dir = self.experiments_dir / experiment_id
        exp_dir.mkdir(exist_ok=True)
        
        return experiment_id
    
    def log_metric(self, metric_name: str, value: float):
        """Log a metric to the current experiment"""
        if self.current_experiment_id is None:
            raise ValueError("No active experiment. Call start_experiment first.")
        
        self.experiment_data['metrics'][metric_name] = value
    
    def log_parameter(self, param_name: str, value: Any):
        """Log a parameter to the current experiment"""
        if self.current_experiment_id is None:
            raise ValueError("No active experiment. Call start_experiment first.")
        
        self.experiment_data['parameters'][param_name] = value
    
    def log_artifact(self, artifact_name: str, artifact_path: str):
        """Log an artifact to the current experiment"""
        if self.current_experiment_id is None:
            raise ValueError("No active experiment. Call start_experiment first.")
        
        # Copy artifact to experiment directory
        exp_artifact_path = self.experiments_dir / self.current_experiment_id / Path(artifact_name).name
        if Path(artifact_path).exists():
            import shutil
            shutil.copy2(artifact_path, exp_artifact_path)
        
        self.experiment_data['artifacts'].append(str(exp_artifact_path))
    
    def end_experiment(self):
        """End the current experiment and save its data"""
        if self.current_experiment_id is None:
            raise ValueError("No active experiment to end.")
        
        self.experiment_data['end_time'] = datetime.now().isoformat()
        
        # Save experiment data to JSON
        exp_file = self.experiments_dir / self.current_experiment_id / "experiment.json"
        with open(exp_file, 'w') as f:
            json.dump(self.experiment_data, f, indent=2, default=str)
        
        # Reset current experiment
        self.current_experiment_id = None
        self.experiment_data = {}
    
    def register_model(self, model, model_name: str, version: str = "1.0", 
                      metrics: Dict[str, float] = None, 
                      description: str = "") -> str:
        """Register a trained model in the model registry"""
        model_id = hashlib.md5(f"{model_name}_{version}_{datetime.now()}".encode()).hexdigest()[:12]
        
        # Create model directory
        model_dir = self.models_dir / model_id
        model_dir.mkdir(exist_ok=True)
        
        # Save model
        model_path = model_dir / f"{model_name}.pkl"
        joblib.dump(model, model_path)
        
        # Save model metadata
        model_metadata = {
            'id': model_id,
            'name': model_name,
            'version': version,
            'registered_at': datetime.now().isoformat(),
            'metrics': metrics or {},
            'description': description,
            'model_path': str(model_path)
        }
        
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(model_metadata, f, indent=2, default=str)
        
        return model_id
    
    def load_model(self, model_id: str):
        """Load a model from the model registry"""
        model_dir = self.models_dir / model_id
        if not model_dir.exists():
            raise ValueError(f"Model with ID {model_id} does not exist")
        
        model_path = model_dir / f"{os.listdir(model_dir)[0]}"  # Get first .pkl file
        for file in os.listdir(model_dir):
            if file.endswith('.pkl'):
                model_path = model_dir / file
                break
        
        return joblib.load(model_path)
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a registered model"""
        model_dir = self.models_dir / model_id
        if not model_dir.exists():
            raise ValueError(f"Model with ID {model_id} does not exist")
        
        metadata_path = model_dir / "metadata.json"
        if not metadata_path.exists():
            raise ValueError(f"Metadata for model {model_id} not found")
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def compare_models(self, model_ids: List[str], metric: str = 'accuracy') -> List[Dict[str, Any]]:
        """Compare models based on a specific metric"""
        comparisons = []
        
        for model_id in model_ids:
            try:
                model_info = self.get_model_info(model_id)
                if metric in model_info.get('metrics', {}):
                    comparisons.append({
                        'model_id': model_id,
                        'model_name': model_info['name'],
                        'version': model_info['version'],
                        'metric': model_info['metrics'][metric],
                        'registered_at': model_info['registered_at']
                    })
            except Exception as e:
                logger.warning(f"Could not compare model {model_id}: {e}")
        
        # Sort by metric (descending for accuracy-like metrics, ascending for error metrics)
        if metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'r2']:
            comparisons.sort(key=lambda x: x['metric'], reverse=True)
        else:  # error metrics like mse, rmse
            comparisons.sort(key=lambda x: x['metric'], reverse=False)
        
        return comparisons
    
    def get_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get model leaderboard based on accuracy or another primary metric"""
        all_models = []
        
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                try:
                    model_info = self.get_model_info(model_dir.name)
                    all_models.append(model_info)
                except:
                    continue  # Skip models with corrupted metadata
        
        # Sort by accuracy if available, otherwise by another metric
        sorted_models = []
        for model in all_models:
            metrics = model.get('metrics', {})
            # Try different metrics in order of preference
            score = metrics.get('accuracy', 0) or metrics.get('r2', 0) or metrics.get('roc_auc', 0) or 0
            model['primary_score'] = score
            sorted_models.append(model)
        
        sorted_models.sort(key=lambda x: x['primary_score'], reverse=True)
        return sorted_models[:top_n]
    
    def evaluate_model_performance(self, model, X_test: pd.DataFrame, y_test: pd.Series, 
                                  problem_type: str = 'classification') -> Dict[str, float]:
        """Evaluate model performance on test data"""
        y_pred = model.predict(X_test)
        
        metrics = {}
        
        if problem_type == 'classification':
            metrics = {
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, average='weighted')),
                'f1': float(f1_score(y_test, y_pred, average='weighted')),
            }
            
            # Add ROC AUC if binary classification
            if len(np.unique(y_test)) == 2:
                try:
                    y_pred_proba = model.predict_proba(X_test)[:, 1]
                    metrics['roc_auc'] = float(roc_auc_score(y_test, y_pred_proba))
                except:
                    pass  # Not all models support predict_proba
        else:  # regression
            metrics = {
                'mse': float(mean_squared_error(y_test, y_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
                'r2': float(r2_score(y_test, y_pred)),
                'mae': float(np.mean(np.abs(y_test - y_pred)))
            }
        
        return metrics
    
    def cross_validate_model(self, model, X: pd.DataFrame, y: pd.Series, 
                           cv: int = 5, problem_type: str = 'classification') -> Dict[str, float]:
        """Perform cross-validation on a model"""
        scoring = 'accuracy' if problem_type == 'classification' else 'r2'
        
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
        
        return {
            'cv_mean': float(scores.mean()),
            'cv_std': float(scores.std()),
            'cv_scores': scores.tolist(),
            'cv_min': float(scores.min()),
            'cv_max': float(scores.max())
        }
    
    def get_experiment_history(self, experiment_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get history of all experiments or experiments with a specific name"""
        experiments = []
        
        for exp_dir in self.experiments_dir.iterdir():
            if exp_dir.is_dir():
                exp_file = exp_dir / "experiment.json"
                if exp_file.exists():
                    with open(exp_file, 'r') as f:
                        exp_data = json.load(f)
                        
                        if experiment_name is None or exp_data['name'] == experiment_name:
                            experiments.append(exp_data)
        
        # Sort by start time
        experiments.sort(key=lambda x: x['start_time'], reverse=True)
        return experiments
    
    def promote_model(self, model_id: str, stage: str = 'production') -> bool:
        """Promote a model to a specific stage (production, staging, etc.)"""
        try:
            model_info = self.get_model_info(model_id)
            
            # Update model metadata with stage
            model_dir = self.models_dir / model_id
            metadata_path = model_dir / "metadata.json"
            
            with open(metadata_path, 'r') as f:
                model_metadata = json.load(f)
            
            model_metadata['stage'] = stage
            model_metadata['promoted_at'] = datetime.now().isoformat()
            
            with open(metadata_path, 'w') as f:
                json.dump(model_metadata, f, indent=2, default=str)
            
            return True
        except Exception as e:
            logger.error(f"Failed to promote model {model_id}: {e}")
            return False
    
    def get_production_models(self) -> List[Dict[str, Any]]:
        """Get all models in production stage"""
        production_models = []
        
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                try:
                    model_info = self.get_model_info(model_dir.name)
                    if model_info.get('stage') == 'production':
                        production_models.append(model_info)
                except:
                    continue  # Skip models with corrupted metadata
        
        return production_models
    
    def create_model_version(self, base_model_id: str, new_model, 
                           new_metrics: Dict[str, float], 
                           version_notes: str = "") -> str:
        """Create a new version of an existing model"""
        try:
            base_model_info = self.get_model_info(base_id)
            
            # Increment version number
            base_version = base_model_info['version']
            version_parts = base_version.split('.')
            if len(version_parts) == 1:
                version_parts.append('0')
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            new_version = '.'.join(version_parts)
            
            # Register new model version
            new_model_id = self.register_model(
                new_model,
                base_model_info['name'],
                new_version,
                new_metrics,
                f"Version upgrade from {base_model_info['version']}. {version_notes}"
            )
            
            return new_model_id
        except Exception as e:
            logger.error(f"Failed to create model version: {e}")
            raise


# Global instance
mlops_manager = MLOpsManager()