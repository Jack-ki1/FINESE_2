"""
⚙️ MLOps - Experiment Tracking & Model Registry
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="MLOPS | FINESE2", page_icon="⚙️", layout="wide")

from utils.session_state import SessionManager
from utils.styling import render_section_header
from modules.mlops_tracker import MLOpsTracker
from modules.ai_assistant import render_ai_settings_sidebar
SessionManager.init()


st.title("⚙️ MLOps Center")



tracker = MLOpsTracker()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🧪 Experiments", "📊 Runs", "🏆 Leaderboard", "📦 Model Registry"])

with tab1:
    render_section_header("Experiments", "Manage your ML experiments")

    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("new_experiment"):
            st.subheader("Create Experiment")
            exp_name = st.text_input("Experiment Name")
            exp_desc = st.text_area("Description")
            exp_tags = st.text_input("Tags (comma-separated)")

            if st.form_submit_button("➕ Create Experiment", type="primary"):
                if exp_name:
                    tags = [t.strip() for t in exp_tags.split(",") if t.strip()]
                    exp_id = tracker.create_experiment(exp_name, exp_desc, tags)
                    st.success(f"Created experiment #{exp_id}")
                    st.rerun()
                else:
                    st.error("Name is required")

    with col2:
        st.subheader("All Experiments")
        experiments = tracker.get_experiments()
        if not experiments.empty:
            st.dataframe(experiments[['id', 'name', 'description', 'status', 'created_at']], 
                        use_container_width=True, hide_index=True)
        else:
            st.info("No experiments yet. Create one to get started.")

with tab2:
    render_section_header("Training Runs", "View and compare model runs")

    experiments = tracker.get_experiments()
    if not experiments.empty:
        selected_exp = st.selectbox("Filter by Experiment", 
                                    ["All"] + experiments['name'].tolist())
        exp_id = None if selected_exp == "All" else experiments[experiments['name'] == selected_exp]['id'].iloc[0]

        runs = tracker.get_runs(exp_id)
        if not runs.empty:
            st.dataframe(runs[['id', 'run_name', 'model_name', 'problem_type', 'metrics', 'created_at']], 
                        use_container_width=True, hide_index=True)

            # Compare runs
            st.subheader("Compare Runs")
            run_ids = st.multiselect("Select runs to compare", runs['id'].tolist())
            if run_ids and st.button("📊 Compare", type="primary"):
                comparison = tracker.compare_runs(run_ids)
                st.dataframe(comparison, use_container_width=True)
        else:
            st.info("No runs logged yet. Train models in the Modeling section.")
    else:
        st.info("Create an experiment first.")

with tab3:
    render_section_header("Leaderboard", "Top performing models")

    problem_type = st.selectbox("Problem Type", ["classification", "regression"])
    metric = st.selectbox("Metric", ["f1", "accuracy", "r2", "rmse"])

    leaderboard = tracker.get_leaderboard(metric=metric, problem_type=problem_type)
    if not leaderboard.empty:
        st.dataframe(leaderboard, use_container_width=True, hide_index=True)
    else:
        st.info("No models on the leaderboard yet.")

with tab4:
    render_section_header("Model Registry", "Registered models")

    models = tracker.get_registered_models()
    if not models.empty:
        st.dataframe(models[['id', 'name', 'version', 'model_name', 'status', 'registered_at']], 
                    use_container_width=True, hide_index=True)

        # Update status
        st.subheader("Update Model Status")
        col1, col2 = st.columns(2)
        with col1:
            model_id = st.number_input("Model ID", min_value=1, step=1)
        with col2:
            new_status = st.selectbox("New Status", ["staging", "production", "archived"])

        if st.button("🔄 Update Status", type="primary"):
            tracker.update_model_status(int(model_id), new_status)
            st.success(f"Updated model {model_id} to {new_status}")
            st.rerun()
    else:
        st.info("No models registered yet.")

# Log current model run if available
if SessionManager.get("models_trained"):
    with st.expander("💾 Log Current Model Run"):
        results = SessionManager.get("models_trained")

        col1, col2 = st.columns(2)
        with col1:
            experiments = tracker.get_experiments()
            if not experiments.empty:
                exp_options = dict(zip(experiments['name'], experiments['id']))
                selected_exp = st.selectbox("Select Experiment", list(exp_options.keys()))
                exp_id = exp_options[selected_exp]
            else:
                st.warning("Create an experiment first")
                exp_id = None

        with col2:
            run_name = st.text_input("Run Name", f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        if exp_id and st.button("💾 Log Run", type="primary"):
            best = results["best_model_result"]
            tracker.log_run(
                experiment_id=exp_id,
                run_name=run_name,
                model_name=results["best_model"],
                problem_type=results["problem_type"],
                params={"test_size": 0.2, "features": results.get("feature_columns", [])},
                metrics=best["metrics"],
                feature_importance=best.get("feature_importance"),
                duration_ms=0
            )
            st.success("Run logged successfully!")
            st.rerun()