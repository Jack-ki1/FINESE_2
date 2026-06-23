"""
FINESE2 - Machine Learning Service
Migrates and enhances engine/ml_modeler.py with user isolation and MLOps integration.
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import json
import logging
import time
from datetime import datetime
from engine.ml_modeler import MLModeler
from app.models.user import Experiment

# NOTE: app/models/user.py currently does NOT define a `Model` ORM class.
# Importing it here breaks app startup.
# We import Model lazily inside methods that require it.

from app.extensions import db

logger = logging.getLogger(__name__)


class MLService:
    """
    Enhanced ML service with user isolation and experiment tracking.
    
    Wraps legacy MLModeler while adding:
    - User-specific model training
    - Database-backed experiment tracking
    - Model registry
    - Performance monitoring
    """
    
    def __init__(self):
        self.modeler = MLModeler()
    
    def train_model(self, df: pd.DataFrame, config: Dict[str, Any], 
                   user_id: int, dataset_id: int) -> Dict[str, Any]:
        """
        Train ML model with full experiment tracking.
        
        Args:
            df: Training data
            config: Model configuration (target, features, model_type, etc.)
            user_id: User training the model
            dataset_id: Source dataset ID
            
        Returns:
            Dictionary with training results and metrics
        """
        start_time = time.time()
        
        try:
            # Create experiment record
            experiment = Experiment(
                name=config.get('experiment_name', f'Experiment_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
                description=config.get('description', ''),
                owner_id=user_id,
                dataset_id=dataset_id,
                status='running',
                params=json.dumps(config)
            )
            db.session.add(experiment)
            db.session.flush()  # Get experiment ID
            
            # Prepare data
            target = config.get('target')
            features = config.get('features', [])
            problem_type = config.get('problem_type', 'classification')
            model_type = config.get('model_type', 'Random Forest')
            
            if not target or not features:
                raise ValueError("Target and features must be specified")
            
            # Split data
            test_size = config.get('test_size', 0.2)
            random_state = config.get('random_state', 42)
            
            X = df[features]
            y = df[target]
            
            # Handle categorical variables
            categorical_cols = X.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
            
            # Train model using legacy engine
            result = self.modeler.train_model(
                df=df,
                target=target,
                features=features,
                problem_type=problem_type,
                model_name=model_type,
                test_size=test_size,
                random_state=random_state
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Update experiment with results
            experiment.status = 'completed'
            experiment.duration_ms = duration_ms
            experiment.metrics = json.dumps(result.get('metrics', {}))
            
            # Save model to registry
            # Model is optional in this codebase; import only when needed.
            from app.models.user import Model  # type: ignore
            model = Model(

                name=f"{model_type}_{experiment.id}",
                version='1.0',
                experiment_id=experiment.id,
                owner_id=user_id,
                model_type=model_type,
                problem_type=problem_type,
                metrics=json.dumps(result.get('metrics', {})),
                feature_importance=json.dumps(result.get('feature_importance', {})),
                status='staging'
            )
            db.session.add(model)
            db.session.commit()
            
            logger.info(f"User {user_id} trained {model_type} model in {duration_ms}ms")
            
            return {
                'experiment_id': experiment.id,
                'model_id': model.id,
                'metrics': result.get('metrics', {}),
                'feature_importance': result.get('feature_importance', {}),
                'duration_ms': duration_ms,
                'status': 'completed'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Model training failed for user {user_id}: {e}")
            
            # Update experiment status to failed
            try:
                experiment.status = 'failed'
                experiment.metrics = json.dumps({'error': str(e)})
                db.session.commit()
            except:
                pass
            
            raise
    
    def get_model_predictions(self, model_id: int, data: pd.DataFrame,
                             user_id: int) -> Dict[str, Any]:
        """
        Generate predictions using a trained model.
        
        Args:
            model_id: Model ID from registry
            data: Data to predict on
            user_id: User making predictions
            
        Returns:
            Dictionary with predictions
        """
        try:
            # Model is optional in this codebase; import only when needed.
            from app.models.user import Model  # type: ignore
            model = Model.query.get(model_id)
            if not model or model.owner_id != user_id:
                raise ValueError("Model not found or access denied")
            
            # Load model and generate predictions
            predictions = self.modeler.predict(model_id, data)
            
            logger.info(f"User {user_id} generated predictions using model {model_id}")
            
            return {
                'predictions': predictions.tolist(),
                'model_id': model_id,
                'model_name': model.name
            }
            
        except Exception as e:
            logger.error(f"Prediction failed for user {user_id}: {e}")
            raise
    
    def compare_models(self, experiment_ids: List[int], user_id: int) -> Dict[str, Any]:
        """Compare multiple experiments/models."""
        try:
            experiments = Experiment.query.filter(
                Experiment.id.in_(experiment_ids),
                Experiment.owner_id == user_id
            ).all()
            
            comparison = []
            for exp in experiments:
                comparison.append({
                    'experiment_id': exp.id,
                    'name': exp.name,
                    'metrics': json.loads(exp.metrics) if exp.metrics else {},
                    'duration_ms': exp.duration_ms,
                    'status': exp.status
                })
            
            return {'comparison': comparison}
            
        except Exception as e:
            logger.error(f"Model comparison failed for user {user_id}: {e}")
            raise


# Singleton instance
ml_service = MLService()
