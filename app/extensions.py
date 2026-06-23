"""
FINESE2 - Flask Extensions Initialization
Centralized extension initialization for the application factory pattern.
"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_socketio import SocketIO

# Initialize extensions (not bound to app yet - will be done in init_extensions)
db = SQLAlchemy()
redis_store = FlaskRedis()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')


def init_extensions(app):
    """
    Initialize and bind all Flask extensions to the application.
    
    Args:
        app: Flask application instance
    """
    # Database (SQLAlchemy ORM)
    db.init_app(app)
    
    # Redis (caching and session storage)
    redis_store.init_app(app)
    
    # Database migrations (Alembic)
    migrate.init_app(app, db)
    
    # JWT authentication
    jwt.init_app(app)
    
    # Rate limiting
    limiter.init_app(app)
    
    # CORS (Cross-Origin Resource Sharing)
    allowed_origins = app.config.get('CORS_ORIGINS', ['*'])
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    )
    
    # WebSocket support (SocketIO for real-time features)
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=False,
        engineio_logger=False
    )
    
    # Register JWT error handlers
    register_jwt_error_handlers(app)


def register_jwt_error_handlers(app):
    """Register custom error handlers for JWT authentication."""
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        from flask import jsonify
        return jsonify({
            'error': 'Invalid token',
            'message': 'The token is invalid or expired'
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({
            'error': 'Token expired',
            'message': 'The token has expired. Please login again.'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        from flask import jsonify
        return jsonify({
            'error': 'Authorization required',
            'message': 'A valid access token is required'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({
            'error': 'Token revoked',
            'message': 'The token has been revoked'
        }), 401
    
    @jwt.needs_fresh_token_loader
    def fresh_token_required_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({
            'error': 'Fresh token required',
            'message': 'A fresh token is required for this operation'
        }), 401
