"""
FINESE2 - MLOps Service
Migrates and enhances engine/mlops_tracker.py with SQLAlchemy integration.
"""
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime
from app.models.user import Experiment

# NOTE: app/models/user.py does NOT define a `Model` ORM class in the current codebase.
# Importing it here breaks app startup. We will import Model lazily inside methods that need it.

from app.extensions import db

logger = logging.getLogger(__name__)


class MLOpsService:
    """
    Enhanced MLOps service using SQLAlchemy instead of SQLite.
    
    Replaces legacy MLOpsTracker with:
    - Database-backed experiment tracking
    - User isolation
    - Advanced querying
    - Model versioning
    """
    
    def create_experiment(self, name: str, description: str, user_id: int,
                         dataset_id: Optional[int] = None,
                         params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new experiment."""
        try:
            experiment = Experiment(
                name=name,
                description=description,
                owner_id=user_id,
                dataset_id=dataset_id,
                status='running',
                params=json.dumps(params) if params else None,
                created_at=datetime.utcnow()
            )
            db.session.add(experiment)
            db.session.commit()
            
            logger.info(f"User {user_id} created experiment: {name}")
            
            return {
                'experiment_id': experiment.id,
                'name': experiment.name,
                'status': experiment.status
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create experiment: {e}")
            raise
    
    def update_experiment(self, experiment_id: int, user_id: int,
                         metrics: Optional[Dict] = None,
                         status: Optional[str] = None,
                         duration_ms: Optional[int] = None) -> Dict[str, Any]:
        """Update experiment with results."""
        try:
            experiment = Experiment.query.get(experiment_id)
            if not experiment or experiment.owner_id != user_id:
                raise ValueError("Experiment not found or access denied")
            
            if metrics:
                experiment.metrics = json.dumps(metrics)
            if status:
                experiment.status = status
            if duration_ms:
                experiment.duration_ms = duration_ms
            
            db.session.commit()
            
            return {
                'experiment_id': experiment.id,
                'status': experiment.status,
                'metrics': json.loads(experiment.metrics) if experiment.metrics else {}
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update experiment: {e}")
            raise
    
    def get_experiments(self, user_id: int, limit: int = 50,
                       offset: int = 0, status: Optional[str] = None) -> List[Dict]:
        """Get user's experiments with filtering."""
        try:
            query = Experiment.query.filter_by(owner_id=user_id)
            
            if status:
                query = query.filter_by(status=status)
            
            experiments = query.order_by(Experiment.created_at.desc())\
                              .limit(limit)\
                              .offset(offset)\
                              .all()
            
            result = []
            for exp in experiments:
                result.append({
                    'id': exp.id,
                    'name': exp.name,
                    'description': exp.description,
                    'status': exp.status,
                    'created_at': exp.created_at.isoformat(),
                    'duration_ms': exp.duration_ms,
                    'metrics': json.loads(exp.metrics) if exp.metrics else {},
                    'params': json.loads(exp.params) if exp.params else {}
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get experiments: {e}")
            raise
    
    def register_model(self, name: str, version: str, experiment_id: int,
                      user_id: int, model_type: str, problem_type: str,
                      metrics: Dict, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Register a model in the model registry."""
        try:
            # Verify experiment ownership
            experiment = Experiment.query.get(experiment_id)
            if not experiment or experiment.owner_id != user_id:
                raise ValueError("Experiment not found or access denied")
            
            from app.models.user import Model  # type: ignore
            model = Model(
                name=name,
                version=version,
                experiment_id=experiment_id,
                owner_id=user_id,
                model_type=model_type,
                problem_type=problem_type,
                metrics=json.dumps(metrics),
                tags=json.dumps(tags) if tags else None,
                status='staging'
            )
            db.session.add(model)
            db.session.commit()
            
            logger.info(f"User {user_id} registered model: {name} v{version}")
            
            return {
                'model_id': model.id,
                'name': model.name,
                'version': model.version,
                'status': model.status
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to register model: {e}")
            raise
    
    def get_models(self, user_id: int, limit: int = 50,
                  offset: int = 0, status: Optional[str] = None) -> List[Dict]:
        """Get user's models from registry."""
        try:
            from app.models.user import Model  # type: ignore
            query = Model.query.filter_by(owner_id=user_id)
            
            if status:
                query = query.filter_by(status=status)
            
            models = query.order_by(Model.registered_at.desc())\
                         .limit(limit)\
                         .offset(offset)\
                         .all()
            
            result = []
            for model in models:
                result.append({
                    'id': model.id,
                    'name': model.name,
                    'version': model.version,
                    'model_type': model.model_type,
                    'problem_type': model.problem_type,
                    'status': model.status,
                    'registered_at': model.registered_at.isoformat(),
                    'metrics': json.loads(model.metrics) if model.metrics else {},
                    'tags': json.loads(model.tags) if model.tags else [],
                    'experiment_id': model.experiment_id
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            raise
    
    def promote_model(self, model_id: int, user_id: int, 
                     new_status: str = 'production') -> Dict[str, Any]:
        """Promote model to production."""
        try:
            from app.models.user import Model  # type: ignore
            model = Model.query.get(model_id)
            if not model or model.owner_id != user_id:
                raise ValueError("Model not found or access denied")
            
            old_status = model.status
            model.status = new_status
            db.session.commit()
            
            logger.info(f"User {user_id} promoted model {model_id} from {old_status} to {new_status}")
            
            return {
                'model_id': model.id,
                'old_status': old_status,
                'new_status': new_status
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to promote model: {e}")
            raise
    
    def get_leaderboard(self, user_id: int, metric: str = 'accuracy',
                       problem_type: Optional[str] = None,
                       limit: int = 10) -> List[Dict]:
        """Get model leaderboard sorted by specified metric."""
        try:
            from app.models.user import Model  # type: ignore
            query = Model.query.filter_by(owner_id=user_id)
            
            if problem_type:
                query = query.filter_by(problem_type=problem_type)
            
            models = query.all()
            
            # Sort by metric
            leaderboard = []
            for model in models:
                metrics = json.loads(model.metrics) if model.metrics else {}
                metric_value = metrics.get(metric, 0)
                
                leaderboard.append({
                    'model_id': model.id,
                    'name': model.name,
                    'version': model.version,
                    'metric': metric,
                    'value': metric_value,
                    'problem_type': model.problem_type,
                    'status': model.status
                })
            
            # Sort descending by metric value
            leaderboard.sort(key=lambda x: x['value'], reverse=True)
            
            return leaderboard[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            raise


# Singleton instance
mlops_service = MLOpsService()
