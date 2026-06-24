"""
FINESE2 - Application Factory
Creates and configures the Flask application instance.
"""
import os
import logging
from flask import Flask, jsonify
from app.config import get_config
from app.extensions import init_extensions, db

# Initialize logger
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """
    Application factory function.
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Configured Flask application instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask app with template and static folders from dashboard
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static')
    )
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Set environment variable for use in other parts of the application
    app.config['ENVIRONMENT'] = config_name
    
    # Initialize extensions (database, Redis, etc.)
    init_extensions(app)
    
    # Register blueprints/routes
    from app.routes import register_blueprints
    register_blueprints(app)
    
    # Import models to ensure they are registered with SQLAlchemy
    # This must happen before db.create_all()
    try:
        from app.models import User, Dataset, Experiment, ModelVersion, Job, AuditLog
    except ImportError as e:
        logger.warning(f"Could not import models: {e}")
    
    # Create database tables
    # IMPORTANT: do not prevent app startup if DB initialization fails.
    # Many environments (tests/dev) should still allow routes like /health.
    with app.app_context():
        try:
            # Ensure instance directory exists
            instance_path = app.config.get('INSTANCE_PATH')
            if instance_path:
                os.makedirs(instance_path, exist_ok=True)
                logger.info(f"Instance directory created/verified at {instance_path}")
            
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.exception(
                "Database initialization failed; continuing startup. "
                "URI=%s cwd=%s Error=%s",
                app.config.get('SQLALCHEMY_DATABASE_URI'),
                os.getcwd(),
                e,
            )
            app.config['DB_INIT_FAILED'] = True
            app.config['DB_INIT_ERROR'] = str(e)
    
    # Register health check endpoint
    register_health_check(app)
    
    # Keep-alive for Hugging Face Spaces (prevents sleep)
    if os.environ.get('SPACE_ID'):
        print("Detected Hugging Face Spaces environment - starting keep-alive")
        import threading
        from app.utils.keep_alive import start_keep_alive
        thread = threading.Thread(target=start_keep_alive, daemon=True)
        thread.start()

    print(f"FINESE2 application created successfully in {config_name} mode")
    
    return app


def register_health_check(app):
    """Register health check endpoints for monitoring."""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for load balancers and monitoring."""
        from app.extensions import db
        import sys
        
        try:
            # Check database connectivity
            db.session.execute(db.text('SELECT 1'))
            
            return jsonify({
                'status': 'healthy',
                'version': '4.0.0',
                'python_version': sys.version.split()[0],
                'database': 'connected',
                'environment': os.environ.get('FLASK_ENV', 'development')
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    @app.route('/ready', methods=['GET'])
    def readiness_check():
        """Readiness check for Kubernetes/load balancers."""
        return jsonify({'ready': True}), 200
