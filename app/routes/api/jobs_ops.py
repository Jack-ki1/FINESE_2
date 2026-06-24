import logging
from flask import Blueprint, jsonify, request
from app.core.jobs import job_queue

logger = logging.getLogger(__name__)

jobs_ops_bp = Blueprint('api_jobs_ops', __name__)


@jobs_ops_bp.route('', methods=['POST'])
def create_job():
    """
    Create a job record.
    Body: { "name": "my_job", "fn": "registered_fn_key", "args": {...} }
    For now we only support a small set of built-in job types.
    """
    body = request.get_json(silent=True) or {}
    name = body.get('name') or 'job'

    # fn key maps to server-side functions
    fn_key = body.get('fn')
    args = body.get('args') or {}

    if not fn_key:
        return jsonify({'error': 'Missing fn (server-side job key)'}), 400

    def job_fn():
        # Built-in job registry (deterministic, no external side effects)
        if fn_key == 'echo':
            return {'echo': args}
        raise ValueError(f'Unknown fn: {fn_key}')

    job = job_queue.create_job(name)
    job_id = job_queue.submit(job, job_fn)

    return jsonify({'job_id': job_id, 'status': 'queued'}), 200


@jobs_ops_bp.route('/<job_id>', methods=['GET'])
def get_job(job_id: str):
    job = job_queue.get_job(job_id)
    if job is None:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job.to_dict()), 200


@jobs_ops_bp.route('/<job_id>/result', methods=['GET'])
def get_job_result(job_id: str):
    job = job_queue.get_job(job_id)
    if job is None:
        return jsonify({'error': 'Job not found'}), 404

    if job.status == 'failed':
        return jsonify({'status': job.status, 'error': job.error, 'trace': job.trace}), 200

    return jsonify({'status': job.status, 'result': job.result}), 200
