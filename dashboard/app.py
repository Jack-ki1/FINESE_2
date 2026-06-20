"""
FINESE2 Dashboard - Flask Application
Single-page application serving HTML templates and API endpoints
"""
import os
import io
import json
import pickle
import uuid
import threading
from datetime import timedelta
from typing import Any, Optional
from functools import lru_cache

import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, send_file, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

# Initialize SocketIO
socketio = SocketIO()

# In-memory storage for DataFrames (replaces Redis)
_dataframe_store = {}
_session_store = {}
_upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def jsonify_numpy(data):
    """Convert data with NumPy types to JSON-serializable format."""
    return json.loads(json.dumps(data, cls=NumpyEncoder))


# ─── Session Manager (In-Memory) ─────────────────────────────────────────────
class SessionManager:
    """In-memory session manager replacing Redis-based storage."""
    
    @staticmethod
    def get_session_id():
        """Get or create session ID."""
        if "sid" not in session:
            session["sid"] = str(uuid.uuid4())
        return session["sid"]
    
    @classmethod
    def set_df(cls, df: pd.DataFrame, source: str = "unknown") -> str:
        """Store DataFrame in memory."""
        sid = cls.get_session_id()
        _dataframe_store[sid] = df
        _session_store.setdefault(sid, {})["data_source"] = source
        return sid
    
    @classmethod
    def get_df(cls) -> Optional[pd.DataFrame]:
        """Retrieve DataFrame from memory."""
        sid = cls.get_session_id()
        return _dataframe_store.get(sid)
    
    @classmethod
    def has_data(cls) -> bool:
        """Check if DataFrame exists."""
        sid = cls.get_session_id()
        return sid in _dataframe_store
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a value from session store."""
        sid = cls.get_session_id()
        return _session_store.get(sid, {}).get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any):
        """Set a value in session store."""
        sid = cls.get_session_id()
        _session_store.setdefault(sid, {})[key] = value
    
    @classmethod
    def reset_data(cls):
        """Clear all data for current session."""
        sid = cls.get_session_id()
        _dataframe_store.pop(sid, None)
        _session_store.pop(sid, None)
    
    @classmethod
    def save_state_snapshot(cls):
        """Save current DataFrame for undo."""
        df = cls.get_df()
        if df is None:
            return
        sid = cls.get_session_id()
        history = _session_store.setdefault(sid, {}).setdefault("history", [])
        history.append(df.copy())
        # Keep last 20 snapshots
        if len(history) > 20:
            history.pop(0)
    
    @classmethod
    def undo(cls) -> bool:
        """Restore previous DataFrame state."""
        sid = cls.get_session_id()
        history = _session_store.get(sid, {}).get("history", [])
        if not history:
            return False
        prev_df = history.pop()
        _dataframe_store[sid] = prev_df
        return True


SM = SessionManager


# ─── Import Engine Modules ────────────────────────────────────────────────────
# These are refactored versions without Streamlit dependencies
from engine.data_manager import DataManager
from engine.eda_engine import EDAEngine
from engine.cleaner import DataCleaner
from engine.visualizer import Visualizer
from engine.analyzer import StatisticalAnalyzer
from engine.ml_modeler import MLModeler
from engine.mlops_tracker import MLOpsTracker
from engine.report_generator import ReportGenerator
from engine.ai_assistant import AIAssistant, Message


def create_data_profile_text(df: pd.DataFrame) -> str:
    """Create a text summary of the dataset for AI context."""
    profile = f"Dataset shape: {df.shape}\n"
    profile += f"Columns: {list(df.columns)}\n"
    profile += f"Data types:\n{df.dtypes.to_string()}\n"
    profile += f"Missing values:\n{df.isnull().sum().to_string()}\n"
    profile += f"\nFirst 5 rows:\n{df.head().to_string()}"
    return profile


# ─── Flask Application Factory ────────────────────────────────────────────────
def create_dashboard_app():
    """Create and configure the Flask dashboard application."""
    
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), "templates"),
                static_folder=os.path.join(os.path.dirname(__file__), "static"))
    
    # Configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "finese2-dev-secret-key")
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
    
    # Enable CORS
    CORS(app, supports_credentials=True)
    
    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")
    
    # Create upload folder
    os.makedirs(_upload_folder, exist_ok=True)
    
    # ─── Main Route (SPA) ─────────────────────────────────────────────────
    @app.route("/")
    def index():
        """Render the single-page dashboard application."""
        return render_template("dashboard.html")
    
    # ─── Data Management API ──────────────────────────────────────────────
    @app.route("/api/data/upload", methods=["POST"])
    def upload_file():
        """Upload and process a data file."""
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        f = request.files["file"]
        options = request.form
        
        sample = options.get("sample_if_large", "true").lower() == "true"
        max_rows = int(options.get("max_rows", 10000))
        file_bytes = f.read()
        fmt = DataManager.detect_format(f.filename)
        
        try:
            if fmt == "csv":
                df = DataManager.load_csv(
                    file_bytes,
                    encoding=options.get("encoding", "utf-8"),
                    sep=options.get("sep", ","),
                    decimal=options.get("decimal", "."),
                    sample_if_large=sample,
                    max_rows=max_rows,
                )
            elif fmt == "excel":
                df, sheets = DataManager.load_excel(
                    file_bytes, sample_if_large=sample, max_rows=max_rows
                )
            elif fmt == "json":
                df = DataManager.load_json(
                    file_bytes, sample_if_large=sample, max_rows=max_rows
                )
            elif fmt == "parquet":
                df = DataManager.load_parquet(
                    file_bytes, sample_if_large=sample, max_rows=max_rows
                )
            else:
                return jsonify({"error": f"Unsupported format: {fmt}"}), 422
            
            df = DataManager.auto_convert_types(df)
            SM.set_df(df, f.filename)
            SM.set("file_name", f.filename)
            
            return jsonify({
                "success": True,
                "shape": list(df.shape),
                "columns": df.columns.tolist(),
                "dtypes": {c: str(t) for c, t in df.dtypes.items()},
                "preview": df.head(10).to_dict(orient="records"),
            })
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/data/sample", methods=["POST"])
    def load_sample():
        """Load sample dataset."""
        df = DataManager.get_sample_data()
        SM.set_df(df, "sample_data")
        SM.set("file_name", "sample_data.csv")
        return jsonify({
            "success": True,
            "shape": list(df.shape),
            "columns": df.columns.tolist(),
            "preview": df.head(10).to_dict(orient="records"),
        })
    
    @app.route("/api/data/sample-dataset", methods=["POST"])
    def load_sample_dataset():
        """Load specific sample dataset (titanic, wine, iris, etc.)."""
        name = request.args.get("name", "default")
        
        # Generate different sample datasets based on name
        if name == "titanic":
            df = DataManager.get_titanic_data()
        elif name == "wine":
            df = DataManager.get_wine_data()
        elif name == "iris":
            df = DataManager.get_iris_data()
        else:
            df = DataManager.get_sample_data()
        
        SM.set_df(df, f"sample_{name}")
        SM.set("file_name", f"{name}_dataset.csv")
        return jsonify({
            "success": True,
            "shape": list(df.shape),
            "columns": df.columns.tolist(),
            "preview": df.head(10).to_dict(orient="records"),
        })
    
    @app.route("/api/data/info", methods=["GET"])
    def get_data_info():
        """Get information about loaded data."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        return jsonify({
            "shape": list(df.shape),
            "columns": df.columns.tolist(),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "missing": df.isnull().sum().to_dict(),
            "duplicates": int(df.duplicated().sum()),
            "file_name": SM.get("file_name"),
            "preview": df.head(20).to_dict(orient="records"),
        })
    
    @app.route("/api/data/export/<fmt>", methods=["GET"])
    def export_data(fmt: str):
        """Export data in specified format."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        exports = DataManager.export_to_formats(df)
        
        if fmt not in exports:
            return jsonify({"error": f"Unknown format: {fmt}"}), 400
        
        mime_map = {
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "json": "application/json",
            "parquet": "application/octet-stream",
        }
        
        return send_file(
            io.BytesIO(exports[fmt]),
            mimetype=mime_map.get(fmt, "application/octet-stream"),
            as_attachment=True,
            download_name=f"export.{fmt}",
        )
    
    @app.route("/api/data/clear", methods=["DELETE"])
    def clear_data():
        """Clear all loaded data."""
        SM.reset_data()
        return jsonify({"success": True})
    
    # ─── EDA API ──────────────────────────────────────────────────────────
    @app.route("/api/eda/profile", methods=["GET"])
    def quick_profile():
        """Generate quick data profile."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        profile = EDAEngine.quick_profile(df)
        issues = EDAEngine.detect_issues(df)
        
        return jsonify(jsonify_numpy({"profile": profile, "issues": issues}))
    
    @app.route("/api/eda/distribution/<column>", methods=["GET"])
    def distribution(column: str):
        """Get distribution plot for a column."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        if column not in df.columns:
            return jsonify({"error": f"Column '{column}' not found"}), 404
        
        fig = EDAEngine.create_distribution_plot(df, column)
        return jsonify(fig.to_json())
    
    @app.route("/api/eda/correlation", methods=["GET"])
    def correlation():
        """Get correlation heatmap."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        fig = EDAEngine.create_correlation_heatmap(df)
        
        if fig is None:
            return jsonify({"error": "Need at least 2 numeric columns"}), 422
        
        return jsonify(fig.to_json())
    
    @app.route("/api/eda/missing-heatmap", methods=["GET"])
    def missing_heatmap():
        """Get missing values heatmap."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        fig = EDAEngine.create_missing_heatmap(df)
        return jsonify(fig.to_json())
    
    @app.route("/api/eda/report/ydata", methods=["POST"])
    def ydata_report():
        """Generate comprehensive ydata-profiling report."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        html = EDAEngine.generate_ydata_report(df)
        
        if html is None:
            return jsonify({"error": "ydata-profiling not installed"}), 500
        
        SM.set("eda_html", html)
        return jsonify({"success": True, "length": len(html)})
    
    @app.route("/api/eda/report/html", methods=["GET"])
    def get_eda_html():
        """Get the generated EDA HTML report."""
        html = SM.get("eda_html")
        if not html:
            return jsonify({"error": "No report generated yet"}), 404
        
        return Response(html, mimetype="text/html")
    
    # ─── Cleaning API ─────────────────────────────────────────────────────
    @app.route("/api/cleaning/recommendations", methods=["GET"])
    def recommendations():
        """Get data cleaning recommendations."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        return jsonify(DataCleaner.get_recommendations(df))
    
    @app.route("/api/cleaning/missing", methods=["POST"])
    def handle_missing():
        """Handle missing values."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        SM.save_state_snapshot()
        
        new_df, log = DataCleaner.handle_missing(
            df,
            strategy=body.get("strategy", "median"),
            columns=body.get("columns"),
            fill_value=body.get("fill_value"),
        )
        
        SM.set_df(new_df, SM.get("data_source"))
        _append_cleaning_log({"step": "missing_values", **log})
        
        return jsonify({"success": True, "log": log, "shape": list(new_df.shape)})
    
    @app.route("/api/cleaning/outliers", methods=["POST"])
    def handle_outliers():
        """Handle outliers."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        SM.save_state_snapshot()
        
        new_df, log = DataCleaner.handle_outliers(
            df,
            method=body.get("method", "clip_iqr"),
            columns=body.get("columns"),
        )
        
        SM.set_df(new_df, SM.get("data_source"))
        _append_cleaning_log({"step": "outliers", **log})
        
        return jsonify({"success": True, "log": log, "shape": list(new_df.shape)})
    
    @app.route("/api/cleaning/duplicates", methods=["POST"])
    def handle_duplicates():
        """Handle duplicate rows."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        SM.save_state_snapshot()
        
        new_df, log = DataCleaner.handle_duplicates(
            df, strategy=body.get("strategy", "drop_all")
        )
        
        SM.set_df(new_df, SM.get("data_source"))
        _append_cleaning_log({"step": "duplicates", **log})
        
        return jsonify({"success": True, "log": log, "shape": list(new_df.shape)})
    
    @app.route("/api/cleaning/scale", methods=["POST"])
    def scale_features():
        """Scale numerical features."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        SM.save_state_snapshot()
        
        new_df, log, _ = DataCleaner.scale_features(
            df,
            method=body.get("method", "standard"),
            columns=body.get("columns"),
        )
        
        SM.set_df(new_df, SM.get("data_source"))
        _append_cleaning_log({"step": "scaling", **log})
        
        return jsonify({"success": True, "log": log, "shape": list(new_df.shape)})
    
    @app.route("/api/cleaning/encode", methods=["POST"])
    def encode_categorical():
        """Encode categorical variables."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        SM.save_state_snapshot()
        
        new_df, log, _ = DataCleaner.encode_categorical(
            df,
            method=body.get("method", "label"),
            columns=body.get("columns"),
            drop_first=body.get("drop_first", True),
        )
        
        SM.set_df(new_df, SM.get("data_source"))
        _append_cleaning_log({"step": "encoding", **log})
        
        return jsonify({"success": True, "log": log, "shape": list(new_df.shape)})
    
    @app.route("/api/cleaning/auto", methods=["POST"])
    def auto_clean():
        """Apply automatic cleaning pipeline."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        SM.save_state_snapshot()
        
        new_df, logs = DataCleaner.auto_clean(df, aggressive=body.get("aggressive", False))
        SM.set_df(new_df, SM.get("data_source"))
        
        for log in logs:
            _append_cleaning_log(log)
        
        return jsonify({"success": True, "logs": logs, "shape": list(new_df.shape)})
    
    @app.route("/api/cleaning/undo", methods=["POST"])
    def undo():
        """Undo last cleaning operation."""
        success = SM.undo()
        return jsonify({"success": success})
    
    @app.route("/api/cleaning/log", methods=["GET"])
    def get_log():
        """Get cleaning history log."""
        return jsonify(SM.get("cleaning_log", []))
    
    def _append_cleaning_log(entry: dict):
        """Append entry to cleaning log."""
        log = SM.get("cleaning_log") or []
        log.append(entry)
        SM.set("cleaning_log", log)
    
    # ─── Visualization API ────────────────────────────────────────────────
    @app.route("/api/viz/bar", methods=["POST"])
    def bar_chart():
        """Create bar chart."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            fig = Visualizer.bar_chart(
                df, x=body["x"], y=body["y"],
                color=body.get("color"), title=body.get("title", ""),
                orientation=body.get("orientation", "v"),
            )
            return jsonify(fig.to_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/viz/line", methods=["POST"])
    def line_chart():
        """Create line chart."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            fig = Visualizer.line_chart(
                df, x=body["x"], y=body["y"],
                color=body.get("color"), title=body.get("title", ""),
            )
            return jsonify(fig.to_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/viz/scatter", methods=["POST"])
    def scatter_chart():
        """Create scatter plot."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            fig = Visualizer.scatter_plot(
                df, x=body["x"], y=body["y"],
                color=body.get("color"), size=body.get("size"),
                title=body.get("title", ""),
            )
            return jsonify(fig.to_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/viz/histogram", methods=["POST"])
    def histogram():
        """Create histogram."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            fig = Visualizer.histogram(
                df, x=body["x"], color=body.get("color"),
                title=body.get("title", ""), nbins=body.get("nbins"),
            )
            return jsonify(fig.to_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/viz/box", methods=["POST"])
    def box_plot():
        """Create box plot."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            fig = Visualizer.box_plot(
                df, y=body["y"], x=body.get("x"),
                color=body.get("color"), title=body.get("title", ""),
            )
            return jsonify(fig.to_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/viz/heatmap", methods=["POST"])
    def heatmap():
        """Create heatmap."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            fig = Visualizer.heatmap(
                df, x=body["x"], y=body["y"], z=body["z"],
                title=body.get("title", ""),
            )
            return jsonify(fig.to_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/viz/pie", methods=["POST"])
    def pie_chart():
        """Create pie chart."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            fig = Visualizer.pie_chart(
                df, names=body["names"], values=body["values"],
                title=body.get("title", ""),
            )
            return jsonify(fig.to_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ─── Analysis API ─────────────────────────────────────────────────────
    @app.route("/api/analysis/summary", methods=["GET"])
    def summary_statistics():
        """Get summary statistics for all columns."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        df = SM.get_df()
        stats = StatisticalAnalyzer.summary_statistics(df)
        return jsonify(stats)
    
    @app.route("/api/analysis/hypothesis-test", methods=["POST"])
    def hypothesis_test():
        """Perform hypothesis testing."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            result = StatisticalAnalyzer.hypothesis_test(
                df,
                test_type=body["test_type"],
                column1=body["column1"],
                column2=body.get("column2"),
                group_column=body.get("group_column"),
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/analysis/correlation-test", methods=["POST"])
    def correlation_test():
        """Perform correlation analysis."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            result = StatisticalAnalyzer.correlation_analysis(
                df,
                columns=body["columns"],
                method=body.get("method", "pearson"),
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/analysis/regression", methods=["POST"])
    def regression_analysis():
        """Perform regression analysis."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            result = StatisticalAnalyzer.regression_analysis(
                df,
                dependent=body["dependent"],
                independent=body["independent"],
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/analysis/anova", methods=["POST"])
    def anova_test():
        """Perform ANOVA test."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            result = StatisticalAnalyzer.anova_test(
                df,
                group_column=body["group_column"],
                value_column=body["value_column"],
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/analysis/normality", methods=["POST"])
    def normality_test():
        """Test for normality."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            result = StatisticalAnalyzer.normality_test(
                df, column=body["column"],
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ─── Modeling API ─────────────────────────────────────────────────────
    @app.route("/api/modeling/train", methods=["POST"])
    def train_models():
        """Train ML models (synchronous for simplicity)."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            results = MLModeler.train_models(
                df,
                target_col=body["target_col"],
                problem_type=body.get("problem_type"),
                models=body.get("models"),
                test_size=body.get("test_size", 0.2),
            )
            
            # Store results
            SM.set("models_trained", results)
            SM.set("target_col", body["target_col"])
            
            return jsonify({"success": True, "results": results})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/modeling/cluster", methods=["POST"])
    def cluster():
        """Perform clustering."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            results = MLModeler.perform_clustering(
                df,
                features=body["features"],
                algorithm=body.get("algorithm", "K-Means"),
                n_clusters=body.get("n_clusters", 3),
            )
            
            SM.set("clustering_results", results)
            return jsonify({"success": True, "results": results})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/modeling/predict", methods=["POST"])
    def predict():
        """Make predictions with trained model."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        models_trained = SM.get("models_trained")
        if not models_trained:
            return jsonify({"error": "No models trained yet"}), 404
        
        try:
            df = SM.get_df()
            best_model_name = models_trained.get("best_model")
            
            predictions = MLModeler.predict_with_model(
                df,
                models_trained["models"][best_model_name]["model"],
                target_col=SM.get("target_col")
            )
            
            return jsonify({
                "predictions": predictions.tolist(),
                "model": best_model_name
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ─── MLOps API ────────────────────────────────────────────────────────
    @app.route("/api/mlops/experiments", methods=["GET"])
    def get_experiments():
        """Get all tracked experiments."""
        tracker = MLOpsTracker()
        experiments = tracker.get_all_experiments()
        return jsonify(experiments)
    
    @app.route("/api/mlops/experiment/<experiment_id>", methods=["GET"])
    def get_experiment(experiment_id: str):
        """Get specific experiment details."""
        tracker = MLOpsTracker()
        experiment = tracker.get_experiment(experiment_id)
        
        if not experiment:
            return jsonify({"error": "Experiment not found"}), 404
        
        return jsonify(experiment)
    
    @app.route("/api/mlops/models", methods=["GET"])
    def get_models():
        """Get model registry."""
        tracker = MLOpsTracker()
        models = tracker.get_model_registry()
        return jsonify(models)
    
    @app.route("/api/mlops/leaderboard", methods=["GET"])
    def get_leaderboard():
        """Get model leaderboard."""
        problem_type = request.args.get("problem_type")
        tracker = MLOpsTracker()
        leaderboard = tracker.get_leaderboard(problem_type=problem_type)
        return jsonify(leaderboard)
    
    @app.route("/api/mlops/compare", methods=["POST"])
    def compare_runs():
        """Compare multiple experiment runs."""
        body = request.get_json()
        run_ids = body.get("run_ids", [])
        
        if not run_ids:
            return jsonify({"error": "No run IDs provided"}), 400
        
        tracker = MLOpsTracker()
        comparison = tracker.compare_runs(run_ids)
        return jsonify(comparison)
    
    @app.route("/api/mlops/metrics/<run_id>", methods=["GET"])
    def get_run_metrics(run_id: str):
        """Get metrics for a specific run."""
        tracker = MLOpsTracker()
        metrics = tracker.get_run_metrics(run_id)
        
        if not metrics:
            return jsonify({"error": "Run not found"}), 404
        
        return jsonify(metrics)
    
    # ─── Reports API ──────────────────────────────────────────────────────
    @app.route("/api/reports/generate/html", methods=["POST"])
    def generate_html_report():
        """Generate HTML report."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            html_content = ReportGenerator.generate_html_report(
                df,
                title=body.get("title", "Data Analysis Report"),
                include_eda=body.get("include_eda", True),
                include_visualizations=body.get("include_visualizations", True),
                include_modeling=body.get("include_modeling", False),
            )
            
            SM.set("report_html", html_content)
            
            return jsonify({
                "success": True,
                "length": len(html_content),
                "message": "HTML report generated"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/reports/download/html", methods=["GET"])
    def download_html_report():
        """Download HTML report."""
        html_content = SM.get("report_html")
        
        if not html_content:
            return jsonify({"error": "No report generated yet"}), 404
        
        return send_file(
            io.BytesIO(html_content.encode('utf-8')),
            mimetype="text/html",
            as_attachment=True,
            download_name="report.html",
        )
    
    @app.route("/api/reports/generate/excel", methods=["POST"])
    def generate_excel_report():
        """Generate Excel report."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            excel_bytes = ReportGenerator.generate_excel_report(
                df, title=body.get("title", "Data Analysis Report"),
            )
            
            return send_file(
                io.BytesIO(excel_bytes),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name="report.xlsx",
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/reports/generate/markdown", methods=["POST"])
    def generate_markdown_report():
        """Generate Markdown report."""
        if not SM.has_data():
            return jsonify({"error": "No data loaded"}), 404
        
        body = request.get_json()
        df = SM.get_df()
        
        try:
            md_content = ReportGenerator.generate_markdown_report(
                df, title=body.get("title", "Data Analysis Report"),
            )
            
            SM.set("report_markdown", md_content)
            
            return jsonify({
                "success": True,
                "length": len(md_content),
                "message": "Markdown report generated"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/reports/download/markdown", methods=["GET"])
    def download_markdown_report():
        """Download Markdown report."""
        md_content = SM.get("report_markdown")
        
        if not md_content:
            return jsonify({"error": "No report generated yet"}), 404
        
        return send_file(
            io.BytesIO(md_content.encode('utf-8')),
            mimetype="text/markdown",
            as_attachment=True,
            download_name="report.md",
        )
    
    # ─── AI Assistant API ─────────────────────────────────────────────────
    @app.route("/api/ai/config", methods=["POST"])
    def configure_ai():
        """Configure AI assistant settings."""
        body = request.get_json()
        
        SM.set("ai_provider", body.get("provider", "openai"))
        SM.set("ai_api_key", body.get("api_key", ""))
        SM.set("ai_base_url", body.get("base_url", ""))
        SM.set("ai_model", body.get("model", "gpt-4o"))
        SM.set("ai_system_prompt", body.get("system_prompt", "You are a data science assistant."))
        
        return jsonify({"success": True, "message": "AI configuration saved"})
    
    @app.route("/api/ai/chat", methods=["POST"])
    def chat_http():
        """Non-streaming chat endpoint (fallback)."""
        body = request.get_json()
        messages = _build_messages(body.get("history", []), body.get("include_data", True))
        assistant = _build_assistant()
        
        try:
            response = assistant.chat(
                messages,
                stream=False,
                temperature=body.get("temperature", 0.7),
                max_tokens=body.get("max_tokens", 4096)
            )
            
            return jsonify({
                "content": response.content,
                "usage": response.usage,
                "model": response.model
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @socketio.on("chat_stream")
    def handle_stream(data):
        """Handle streaming chat via WebSocket."""
        room = data.get("room", request.sid)
        join_room(room)
        
        messages = _build_messages(data.get("history", []), data.get("include_data", True))
        assistant = _build_assistant()
        
        try:
            for chunk in assistant.chat(
                messages,
                stream=True,
                temperature=data.get("temperature", 0.7),
                max_tokens=data.get("max_tokens", 4096)
            ):
                emit("chat_chunk", {"chunk": chunk, "done": False}, room=room)
            
            emit("chat_chunk", {"chunk": "", "done": True}, room=room)
        except Exception as e:
            emit("chat_error", {"error": str(e)}, room=room)
    
    def _build_assistant() -> AIAssistant:
        """Build AI assistant from session config."""
        return AIAssistant(
            provider_name=SM.get("ai_provider", "openai"),
            api_key=SM.get("ai_api_key", ""),
            base_url=SM.get("ai_base_url", ""),
            model=SM.get("ai_model", "gpt-4o"),
        )
    
    def _build_messages(history: list, include_data: bool) -> list:
        """Build message list with optional data context."""
        system_content = SM.get("ai_system_prompt", "You are a data science assistant.")
        
        if include_data and SM.has_data():
            df = SM.get_df()
            system_content += f"\n\nCURRENT DATASET:\n{create_data_profile_text(df)}"
        
        messages = [Message(role="system", content=system_content)]
        
        for msg in history[-10:]:
            messages.append(Message(role=msg["role"], content=msg["content"]))
        
        return messages
    
    # ─── System API ───────────────────────────────────────────────────────
    @app.route("/api/system/status", methods=["GET"])
    def system_status():
        """Get system status."""
        return jsonify({
            "status": "running",
            "version": "3.0",
            "data_loaded": SM.has_data(),
            "file_name": SM.get("file_name") if SM.has_data() else None,
        })
    
    @app.route("/api/system/initialize", methods=["POST"])
    def initialize_system():
        """Initialize system (create directories, etc.)."""
        os.makedirs(_upload_folder, exist_ok=True)
        return jsonify({
            "success": True,
            "message": "System initialized successfully"
        })
    
    return app


if __name__ == "__main__":
    app = create_dashboard_app()
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
