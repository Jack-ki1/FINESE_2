import os
from flask import Flask, render_template, session
from flask_session import Session
from datetime import timedelta
import state
from core.dataset_store import DatasetStore
from routes import (
    data_bp, review_bp, cleaning_bp, charts_bp, 
    chatbot_bp, ml_bp, sql_bp, export_bp, mlops_bp
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB uploads

Session(app)
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/exports', exist_ok=True)
os.makedirs('static/reports', exist_ok=True)

# Initialize dataset store
app.dataset_store = DatasetStore(base_path='static/uploads')

# Register blueprints
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

@app.route('/')
def index():
    return render_template('review.html', active_tab='review')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
