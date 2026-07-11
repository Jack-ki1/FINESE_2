import os
import traceback
import sys
from flask import Flask, render_template, session
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import state
from config import Config
from routes import (
    data_bp, review_bp, cleaning_bp, charts_bp, 
    chatbot_bp, ml_bp, sql_bp, export_bp, mlops_bp
)

try:
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config())

    Session(app)

    # Initialize rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per minute"],
        storage_uri="memory://"
    )

    # Create directories early
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/exports', exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs(str(app.config['SESSION_FILE_DIR']), exist_ok=True)

    # Initialize dataset store early but with error handling
    try:
        from core.dataset_store import DatasetStore
        app.dataset_store = DatasetStore(base_path=str(app.config['UPLOAD_FOLDER']))
    except Exception as e:
        print(f"Error initializing dataset store: {e}")
        print(traceback.format_exc())
        sys.exit(1)

    # Import and register blueprints
    from routes import (
        data_bp, review_bp, cleaning_bp, charts_bp, 
        chatbot_bp, ml_bp, sql_bp, export_bp, mlops_bp
    )
    
    app.register_blueprint(data_bp)
    app.register_blueprint(review_bp, url_prefix='/review')
    app.register_blueprint(cleaning_bp, url_prefix='/cleaning')
    app.register_blueprint(charts_bp, url_prefix='/charts')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(ml_bp, url_prefix='/ml')
    app.register_blueprint(sql_bp, url_prefix='/sql')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(mlops_bp, url_prefix='/mlops')

    @app.before_request
    def init_session():
        if 'initialized' not in session:
            for key, val in state.DEFAULT_STATE.items():
                session[key] = val
            session['initialized'] = True
            session.permanent = True

    @app.context_processor
    def inject_dataset():
        """Inject current dataset info into all templates."""
        from core.dataset_store import get_current_dataset
        ds = get_current_dataset()
        return {"current_dataset": ds}

    @app.route('/')
    def index():
        return render_template('review.html', active_tab='review')

except Exception as e:
    print(f"An error occurred during application startup: {e}")
    print("Full traceback:")
    print(traceback.format_exc())
    sys.exit(1)

if __name__ == '__main__':
    app.run(debug=True, port=5000)