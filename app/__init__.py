"""
FINESE2 - Flask Application Factory
Professional data intelligence platform with authentication and MLOps
"""
import os
import logging
from flask import Flask, jsonify
from app.config import Config
from app.extensions import init_extensions
from app.routes import register_blueprints


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=None):
    # Ensure SQLite instance folder exists so sqlite:///instance/*.db can be created
    try:
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
        os.makedirs(instance_path, exist_ok=True)
    except Exception:
        pass

    """
    Application factory pattern for FINESE2.
    
    Args:
        config_class: Configuration class to use (defaults to environment-based)
    
    Returns:
        Configured Flask application instance
    """
    # Determine configuration based on environment
    if config_class is None:
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'production':
            from app.config import ProductionConfig
            config_class = ProductionConfig
        elif env == 'testing':
            from app.config import TestingConfig
            config_class = TestingConfig
        else:
            from app.config import DevelopmentConfig
            config_class = DevelopmentConfig
    
    # Create Flask app with template and static folders from dashboard
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static')
    )
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Initialize extensions (database, JWT, Redis, etc.)
    init_extensions(app)
    
    # Register blueprints (routes)
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register health check endpoint
    register_health_check(app)
    
    # Keep-alive for Hugging Face Spaces (prevents sleep)
    if os.environ.get('SPACE_ID'):
        logger.info("Detected Hugging Face Spaces environment - starting keep-alive")
        import threading
        from app.utils.keep_alive import start_keep_alive
        thread = threading.Thread(target=start_keep_alive, daemon=True)
        thread.start()
    
    logger.info(f"FINESE2 application created successfully in {env} mode")
    
    return app


def register_error_handlers(app):
    """Register global error handlers for consistent API responses."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method not allowed', 'message': 'HTTP method not supported'}), 405
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({'error': 'Rate limit exceeded', 'message': 'Too many requests'}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return jsonify({'error': 'Service unavailable', 'message': 'Service temporarily unavailable'}), 503


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
                'version': '3.0.0',
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
