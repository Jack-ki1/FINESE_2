"""
MLOps Tracker - Lightweight experiment tracking and model registry
Uses SQLite for persistence (no external MLflow server required)
Refactored: No Streamlit dependencies
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class MLOpsTracker:
    """Lightweight MLOps tracking using local SQLite."""

    def __init__(self, db_path: str = "finese2_mlops.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'running', tags TEXT, params TEXT, metrics TEXT, artifact_path TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, experiment_id INTEGER,
                run_name TEXT, model_name TEXT, problem_type TEXT,
                params TEXT, metrics TEXT, feature_importance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, duration_ms INTEGER,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                version TEXT, run_id INTEGER, model_type TEXT, metrics TEXT,
                tags TEXT, registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'staging',
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        """)
        conn.commit()
        conn.close()

    def get_all_experiments(self) -> List[Dict]:
        """Get all experiments as list of dicts."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_experiment(self, experiment_id: int) -> Optional[Dict]:
        """Get specific experiment."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_model_registry(self) -> List[Dict]:
        """Get all registered models."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mr.*, r.model_name, r.problem_type, e.name as experiment_name
            FROM model_registry mr
            JOIN runs r ON mr.run_id = r.id
            JOIN experiments e ON r.experiment_id = e.id
            ORDER BY mr.registered_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_leaderboard(self, problem_type: Optional[str] = None) -> List[Dict]:
        """Get model leaderboard."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if problem_type:
            cursor.execute("""
                SELECT r.*, e.name as experiment_name FROM runs r
                JOIN experiments e ON r.experiment_id = e.id
                WHERE r.problem_type = ? ORDER BY r.created_at DESC
            """, (problem_type,))
        else:
            cursor.execute("""
                SELECT r.*, e.name as experiment_name FROM runs r
                JOIN experiments e ON r.experiment_id = e.id
                ORDER BY r.created_at DESC
            """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        results = []
        for row in rows:
            metrics = json.loads(row['metrics']) if row['metrics'] else {}
            results.append({
                'run_id': row['id'], 'experiment': row['experiment_name'],
                'model': row['model_name'], 'run_name': row['run_name'],
                'metrics': metrics, 'created_at': row['created_at']
            })
        return results

    def compare_runs(self, run_ids: List[int]) -> List[Dict]:
        """Compare multiple runs side by side."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(run_ids))
        cursor.execute(f"""
            SELECT id, run_name, model_name, problem_type, metrics, created_at
            FROM runs WHERE id IN ({placeholders})
        """, run_ids)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        results = []
        for row in rows:
            metrics = json.loads(row['metrics']) if row['metrics'] else {}
            results.append({
                'run_id': row['id'], 'run_name': row['run_name'],
                'model_name': row['model_name'], 'metrics': metrics
            })
        return results

    def get_run_metrics(self, run_id: int) -> Optional[Dict]:
        """Get metrics for a specific run."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        row_dict = dict(row)
        row_dict['metrics'] = json.loads(row_dict['metrics']) if row_dict['metrics'] else {}
        row_dict['feature_importance'] = json.loads(row_dict['feature_importance']) if row_dict['feature_importance'] else {}
        return row_dict
