"""
FINESE2 - Database Models
SQLAlchemy ORM models for data persistence
"""
from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user, viewer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    datasets = db.relationship('Dataset', backref='owner', lazy=True)
    experiments = db.relationship('Experiment', backref='owner', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class Dataset(db.Model):
    """Dataset model for tracking uploaded datasets."""
    __tablename__ = 'datasets'
    
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rows = db.Column(db.Integer)
    columns = db.Column(db.Integer)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # in bytes
    file_type = db.Column(db.String(20))  # csv, excel, json, parquet
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    metadata_json = db.Column(db.JSON)
    version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='active')  # active, archived, deleted
    
    # Relationships
    experiments = db.relationship('Experiment', backref='dataset', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rows': self.rows,
            'columns': self.columns,
            'file_type': self.file_type,
            'created_at': self.created_at.isoformat(),
            'version': self.version,
            'status': self.status
        }


class Experiment(db.Model):
    """ML experiment tracking model."""
    __tablename__ = 'experiments'
    
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    dataset_id = db.Column(db.String(64), db.ForeignKey('datasets.id'))
    algorithm = db.Column(db.String(100))
    problem_type = db.Column(db.String(50))  # classification, regression
    hyperparameters = db.Column(db.JSON)
    metrics = db.Column(db.JSON)
    model_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='running')  # running, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    versions = db.relationship('ModelVersion', backref='experiment', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'algorithm': self.algorithm,
            'problem_type': self.problem_type,
            'metrics': self.metrics,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class ModelVersion(db.Model):
    """Model versioning for MLOps."""
    __tablename__ = 'model_versions'
    
    id = db.Column(db.String(64), primary_key=True)
    experiment_id = db.Column(db.String(64), db.ForeignKey('experiments.id'))
    version_number = db.Column(db.Integer, nullable=False)
    model_path = db.Column(db.String(500))
    metrics = db.Column(db.JSON)
    is_production = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'version_number': self.version_number,
            'metrics': self.metrics,
            'is_production': self.is_production,
            'created_at': self.created_at.isoformat()
        }


class Job(db.Model):
    """Background job tracking."""
    __tablename__ = 'jobs'
    
    id = db.Column(db.String(64), primary_key=True)
    job_type = db.Column(db.String(50))  # training, cleaning, eda, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    progress = db.Column(db.Float, default=0.0)  # 0-100
    parameters = db.Column(db.JSON)
    result = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_type': self.job_type,
            'status': self.status,
            'progress': self.progress,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class AuditLog(db.Model):
    """Audit trail for tracking user actions."""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.String(64))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'created_at': self.created_at.isoformat()
        }
