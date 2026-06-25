from flask import Blueprint, render_template, session, jsonify, request, current_app
import uuid
import threading

bp = Blueprint('ml', __name__)
jobs = {}

@bp.route('/')
def ml_page():
    return render_template('ml.html', active_tab='ml')

@bp.route('/api/train', methods=['POST'])
def train():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'running', 'progress': 0, 'result': None}
    session['ml_job_id'] = job_id
    def run_job():
        import time
        for i in range(5):
            time.sleep(1)
            jobs[job_id]['progress'] = (i + 1) * 20
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['result'] = {'accuracy': 0.95, 'model': 'RandomForest'}
    threading.Thread(target=run_job).start()
    return jsonify({'job_id': job_id})

@bp.route('/api/status/<job_id>', methods=['GET'])
def status(job_id):
    return jsonify(jobs.get(job_id, {}))
