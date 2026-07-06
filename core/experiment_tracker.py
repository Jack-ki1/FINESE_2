import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path("models/experiments.db")

def _get_conn():
    """Get database connection and ensure table exists."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            name TEXT,
            params TEXT,
            metrics TEXT,
            status TEXT,
            tags TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn

def log_experiment(name, params=None, metrics=None, status='completed', tags=None):
    """Log an experiment to SQLite database."""
    exp_id = str(uuid.uuid4())
    conn = _get_conn()
    conn.execute(
        "INSERT INTO experiments VALUES (?,?,?,?,?,?,?)",
        (exp_id, name,
         json.dumps(params or {}),
         json.dumps(metrics or {}),
         status,
         json.dumps(tags or []),
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return exp_id

def list_experiments(limit=100, tag=None):
    """List experiments from database."""
    conn = _get_conn()
    if tag:
        rows = conn.execute(
            "SELECT * FROM experiments WHERE tags LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f'%"{tag}"%', limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM experiments ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    cols = ['id', 'name', 'params', 'metrics', 'status', 'tags', 'timestamp']
    return [dict(zip(cols, r)) for r in rows]

def delete_experiment(exp_id):
    """Delete an experiment from database."""
    conn = _get_conn()
    conn.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))
    conn.commit()
    conn.close()
