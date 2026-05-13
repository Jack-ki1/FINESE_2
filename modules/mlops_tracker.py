"""
MLOps Tracker - Lightweight experiment tracking and model registry
Uses SQLite for persistence (no external MLflow server required)
"""
import sqlite3
import json
import pickle
import base64
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import streamlit as st

class MLOpsTracker:
    """Lightweight MLOps tracking using local SQLite."""

    def __init__(self, db_path: str = "data_all1_mlops.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'running',
                tags TEXT,
                params TEXT,
                metrics TEXT,
                artifact_path TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                run_name TEXT,
                model_name TEXT,
                problem_type TEXT,
                params TEXT,
                metrics TEXT,
                feature_importance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_ms INTEGER,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT,
                run_id INTEGER,
                model_type TEXT,
                metrics TEXT,
                tags TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'staging',
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_experiment(self, name: str, description: str = "", tags: List[str] = None) -> int:
        """Create a new experiment."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO experiments (name, description, tags, params, metrics)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, json.dumps(tags or []), "{}", "{}"))

        exp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return exp_id

    def log_run(self, experiment_id: int, run_name: str, model_name: str, 
                problem_type: str, params: Dict, metrics: Dict, 
                feature_importance: Optional[Dict] = None, duration_ms: int = 0) -> int:
        """Log a model training run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO runs (experiment_id, run_name, model_name, problem_type, 
                            params, metrics, feature_importance, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment_id, run_name, model_name, problem_type,
            json.dumps(params, default=str),
            json.dumps(metrics, default=str),
            json.dumps(feature_importance or {}, default=str),
            duration_ms
        ))

        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return run_id

    def register_model(self, name: str, version: str, run_id: int, 
                       model_type: str, metrics: Dict, tags: List[str] = None) -> int:
        """Register a model in the model registry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO model_registry (name, version, run_id, model_type, metrics, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, version, run_id, model_type, json.dumps(metrics, default=str), json.dumps(tags or [])))

        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return model_id

    def get_experiments(self) -> pd.DataFrame:
        """Get all experiments."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM experiments ORDER BY created_at DESC", conn)
        conn.close()
        return df

    def get_runs(self, experiment_id: Optional[int] = None) -> pd.DataFrame:
        """Get runs, optionally filtered by experiment."""
        conn = sqlite3.connect(self.db_path)
        if experiment_id:
            df = pd.read_sql_query(
                "SELECT * FROM runs WHERE experiment_id = ? ORDER BY created_at DESC",
                conn, params=(experiment_id,)
            )
        else:
            df = pd.read_sql_query("SELECT * FROM runs ORDER BY created_at DESC", conn)
        conn.close()
        return df

    def get_registered_models(self) -> pd.DataFrame:
        """Get all registered models."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
            SELECT mr.*, r.model_name, r.problem_type, e.name as experiment_name
            FROM model_registry mr
            JOIN runs r ON mr.run_id = r.id
            JOIN experiments e ON r.experiment_id = e.id
            ORDER BY mr.registered_at DESC
        """, conn)
        conn.close()
        return df

    def update_model_status(self, model_id: int, status: str):
        """Update model status (staging, production, archived)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE model_registry SET status = ? WHERE id = ?", (status, model_id))
        conn.commit()
        conn.close()

    def compare_runs(self, run_ids: List[int]) -> pd.DataFrame:
        """Compare multiple runs side by side."""
        conn = sqlite3.connect(self.db_path)
        placeholders = ','.join('?' * len(run_ids))
        df = pd.read_sql_query(f"""
            SELECT id, run_name, model_name, problem_type, metrics, created_at
            FROM runs WHERE id IN ({placeholders})
        """, conn, params=run_ids)
        conn.close()

        metrics_data = []
        for _, row in df.iterrows():
            metrics = json.loads(row['metrics'])
            metrics['run_id'] = row['id']
            metrics['run_name'] = row['run_name']
            metrics['model_name'] = row['model_name']
            metrics_data.append(metrics)

        return pd.DataFrame(metrics_data)

    def get_leaderboard(self, metric: str = "f1", problem_type: str = "classification") -> pd.DataFrame:
        """Get leaderboard for a specific metric."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
            SELECT r.*, e.name as experiment_name
            FROM runs r
            JOIN experiments e ON r.experiment_id = e.id
            WHERE r.problem_type = ?
            ORDER BY r.created_at DESC
        """, conn, params=(problem_type,))
        conn.close()

        results = []
        for _, row in df.iterrows():
            metrics = json.loads(row['metrics'])
            results.append({
                'run_id': row['id'],
                'experiment': row['experiment_name'],
                'model': row['model_name'],
                'run_name': row['run_name'],
                metric: metrics.get(metric, None),
                'created_at': row['created_at']
            })

        result_df = pd.DataFrame(results)
        if metric in result_df.columns:
            result_df = result_df.sort_values(metric, ascending=False)
        return result_df
