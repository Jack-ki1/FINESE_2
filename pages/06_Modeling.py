"""
🤖 Modeling - Machine Learning Model Training
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, r2_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


st.set_page_config(page_title="MODELLING | FINESE2", page_icon="🤖", layout="wide")

from utils.session_state import SessionManager
from utils.styling import render_section_header
from modules.ml_modeler import MLModeler
from modules.ai_assistant import render_ai_settings_sidebar

SessionManager.init()

st.title("🤖 Machine Learning")

if not SessionManager.has_data():
    st.warning("⚠️ No data loaded. Please load data in the Data section first.")
    st.stop()

df = SessionManager.get_df()

# Create tabs for different ML approaches
tab_supervised, tab_unsupervised = st.tabs(["Supervised Learning", "Unsupervised Learning"])

with tab_supervised:
    # Problem Type Selection
    render_section_header("Supervised Learning", "Choose your problem type")
    
    problem_type = st.selectbox(
        "Select Problem Type", 
        ["Choose...", "Classification", "Regression"],
        format_func=lambda x: "Choose..." if x == "Choose..." else x,
        key="supervised_problem_type"
    )
    
    if problem_type != "Choose...":
        st.subheader(f"Selected: {problem_type}")
        
        # Model Configuration
        render_section_header(f"{problem_type} Configuration", "")

        col1, col2, col3 = st.columns(3)
        with col1:
            target_col = st.selectbox("Target Column", df.columns, key="sup_target_col")
        with col2:
            test_size = st.slider("Test Size", 0.1, 0.5, 0.2, 0.05)
        with col3:
            # Add advanced options if needed
            advanced_options = st.checkbox("Show Advanced Options", value=False)

        # Feature selection
        all_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        all_categorical = df.select_dtypes(include=['object', 'category']).columns.tolist()
        available_features = all_numeric + all_categorical

        selected_features = st.multiselect("Feature Columns", available_features, 
                                          default=all_numeric[:min(5, len(all_numeric))],
                                          key="sup_selected_features")

        if not selected_features:
            st.warning("Please select at least one feature column")
            st.stop()

        # Prepare subset
        df_model = df[selected_features + [target_col]].dropna()

        # Model Selection
        st.subheader("Model Selection")
        
        # Get all available models from MLModeler
        if problem_type == "Classification":
            all_available_models = list(MLModeler.CLASSIFICATION_MODELS.keys())
        else:
            all_available_models = list(MLModeler.REGRESSION_MODELS.keys())
        
        # Allow user to select which models to train
        selected_models = st.multiselect(
            f"Select {problem_type} Models to Train", 
            options=all_available_models,
            default=all_available_models,  # Default to all models
            help=f"Choose which {problem_type.lower()} models you want to train and compare",
            key="sup_selected_models"
        )
        
        if st.button(f"🚀 Train Selected {problem_type} Models", type="primary", use_container_width=True, key="sup_train_btn"):
            with st.spinner(f"Training {problem_type.lower()} models... This may take a few minutes."):
                results = MLModeler.auto_train(df_model, target_col, problem_type=problem_type.lower(), 
                                              models=selected_models, test_size=test_size)

                SessionManager.set("supervised_models_trained", results)
                SessionManager.set("sup_target_col", target_col)
                SessionManager.set("sup_problem_type", results["problem_type"])

                st.success(f"✅ Training complete! Best model: **{results['best_model']}**")
                st.rerun()

# Hyperparameter Tuning Section
with st.expander("⚙️ Hyperparameter Tuning"):
    st.subheader("Hyperparameter Optimization")
    
    # Tabs for Supervised and Unsupervised tuning
    tune_tabs = st.tabs(["Supervised Tuning", "Unsupervised Tuning"])
    
    with tune_tabs[0]:  # Supervised Tuning
        col1, col2 = st.columns(2)
        with col1:
            # Include more models in hyperparameter tuning options
            model_for_tuning = st.selectbox("Model for tuning", 
                                           ["Random Forest", "XGBoost", "SVM", "Gradient Boosting", "Decision Tree"], 
                                           key="hp_model")
        with col2:
            if st.button("🔬 Optimize Parameters", type="primary", key="hp_optimize_btn"):
                with st.spinner(f"Tuning {model_for_tuning} parameters..."):
                    try:
                        # Get data from supervised section if available
                        sup_target_col = SessionManager.get("sup_target_col")
                        if sup_target_col:
                            # Use the data from the supervised section
                            all_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
                            all_categorical = df.select_dtypes(include=['object', 'category']).columns.tolist()
                            available_features = all_numeric + all_categorical
                            
                            selected_features = SessionManager.get("sup_selected_features", all_numeric[:min(5, len(all_numeric))])
                            df_model = df[selected_features + [sup_target_col]].dropna()
                            
                            hp_results = MLModeler.hyperparameter_tuning(
                                df_model, sup_target_col, model_for_tuning, 
                                SessionManager.get("sup_problem_type", "classification")
                            )
                            SessionManager.set("hp_results", hp_results)
                            st.success(f"✅ Hyperparameter tuning complete for {model_for_tuning}!")
                        else:
                            st.warning("Please train a model in the Supervised Learning section first.")
                    except Exception as e:
                        st.error(f"Error during hyperparameter tuning: {str(e)}")

        if SessionManager.get("hp_results"):
            hp_results = SessionManager.get("hp_results")
            st.subheader(f"Best Parameters for {model_for_tuning}")
            st.json(hp_results["best_params"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Best CV Score", f"{hp_results['best_score']:.4f}")
            with col2:
                st.metric("Model Type", model_for_tuning)
    
    with tune_tabs[1]:  # Unsupervised Tuning
        st.info("Unsupervised hyperparameter tuning coming soon!")
        st.markdown("""
        In future versions, you'll be able to tune hyperparameters for unsupervised learning methods such as:
        - Number of clusters (k-means, hierarchical clustering)
        - Epsilon and minimum samples (DBSCAN)
        - Number of components (PCA, t-SNE)
        - Contamination parameter (anomaly detection)
        """)


# Ensemble Prediction Section
with st.expander("🧩 Ensemble Prediction"):
    st.subheader("Ensemble Multiple Models")
    
    # Tabs for Supervised and Unsupervised ensembles
    ensemble_tabs = st.tabs(["Supervised Ensemble", "Unsupervised Ensemble"])
    
    with ensemble_tabs[0]:  # Supervised Ensemble
        # Include more models in ensemble options
        ensemble_models = st.multiselect(
            "Select models for ensemble", 
            ["Random Forest", "Gradient Boosting", "SVM", "K-Nearest Neighbors", "Decision Tree", "Logistic Regression", 
             "AdaBoost", "Extra Trees", "XGBoost", "LightGBM"],
            default=["Random Forest", "Gradient Boosting"],
            key="ensemble_models"
        )
        
        if st.button("🔮 Create Ensemble", type="primary", key="create_ensemble_btn"):
            with st.spinner("Creating ensemble prediction..."):
                try:
                    # Get data from supervised section if available
                    sup_target_col = SessionManager.get("sup_target_col")
                    if sup_target_col:
                        # Use the data from the supervised section
                        all_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
                        all_categorical = df.select_dtypes(include=['object', 'category']).columns.tolist()
                        available_features = all_numeric + all_categorical
                        
                        selected_features = SessionManager.get("sup_selected_features", all_numeric[:min(5, len(all_numeric))])
                        df_model = df[selected_features + [sup_target_col]].dropna()
                        
                        ensemble_results = MLModeler.ensemble_prediction(
                            df_model, sup_target_col, ensemble_models
                        )
                        SessionManager.set("ensemble_results", ensemble_results)
                        st.success("✅ Ensemble prediction complete!")
                    else:
                        st.warning("Please train a model in the Supervised Learning section first.")
                except Exception as e:
                    st.error(f"Error during ensemble prediction: {str(e)}")

        if SessionManager.get("ensemble_results"):
            ensemble_results = SessionManager.get("ensemble_results")
            st.subheader("Ensemble Results")
            
            col1, col2, col3, col4 = st.columns(4)
            if ensemble_results['problem_type'] == 'classification':
                col1.metric("Accuracy", f"{ensemble_results['metrics']['accuracy']:.4f}")
                col2.metric("Precision", f"{ensemble_results['metrics']['precision']:.4f}")
                col3.metric("Recall", f"{ensemble_results['metrics']['recall']:.4f}")
                col4.metric("F1 Score", f"{ensemble_results['metrics']['f1']:.4f}")
            else:
                col1.metric("R²", f"{ensemble_results['metrics']['r2']:.4f}")
                col2.metric("RMSE", f"{ensemble_results['metrics']['rmse']:.4f}")
                col3.metric("MAE", f"{ensemble_results['metrics']['mae']:.4f}")
                col4.metric("MSE", f"{ensemble_results['metrics']['mse']:.4f}")
    
    with ensemble_tabs[1]:  # Unsupervised Ensemble
        st.info("Unsupervised ensemble methods coming soon!")
        st.markdown("""
        Future ensemble capabilities for unsupervised learning will include:
        - Combining multiple clustering algorithms
        - Consensus clustering approaches
        - Anomaly detection ensemble methods
        - Hybrid clustering techniques
        """)


# Display Supervised Results
if SessionManager.get("supervised_models_trained"):
    results = SessionManager.get("supervised_models_trained")

    render_section_header("Model Results", f"Problem Type: {results['problem_type'].title()}")

    # Comparison table
    comparison_data = []
    for name, result in results["models"].items():
        row = {"Model": name}
        row.update(result["metrics"])
        row["CV Mean"] = f"{result['cv_mean']:.4f}"
        row["CV Std"] = f"{result['cv_std']:.4f}"
        comparison_data.append(row)

    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    # Best model details
    best = results["best_model_result"]

    st.subheader(f"🏆 Best Model: {results['best_model']}")

    if results['problem_type'] == 'classification':
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Accuracy", f"{best['metrics']['accuracy']:.4f}")
        col2.metric("Precision", f"{best['metrics']['precision']:.4f}")
        col3.metric("Recall", f"{best['metrics']['recall']:.4f}")
        col4.metric("F1 Score", f"{best['metrics']['f1']:.4f}")

        # Confusion Matrix
        if 'confusion_matrix' in best['metrics']:
            cm = np.array(best['metrics']['confusion_matrix'])
            fig = px.imshow(cm, text_auto=True, color_continuous_scale='Blues',
                          title="Confusion Matrix", template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("R²", f"{best['metrics']['r2']:.4f}")
        col2.metric("RMSE", f"{best['metrics']['rmse']:.4f}")
        col3.metric("MAE", f"{best['metrics']['mae']:.4f}")
        col4.metric("MSE", f"{best['metrics']['mse']:.4f}")

        # Actual vs Predicted
        # Create a DataFrame for the plot to ensure compatibility with plotly
        plot_df = pd.DataFrame({
            'Actual': best['actual'].flatten() if hasattr(best['actual'], 'flatten') else np.ravel(best['actual']),
            'Predicted': best['predictions'].flatten() if hasattr(best['predictions'], 'flatten') else np.ravel(best['predictions'])
        })
        
        fig = px.scatter(plot_df, x='Actual', y='Predicted', 
                        title="Actual vs Predicted", template="plotly_dark",
                        labels={'x': 'Actual', 'y': 'Predicted'})
        # Add perfect prediction line
        min_val = min(plot_df['Actual'].min(), plot_df['Predicted'].min())
        max_val = max(plot_df['Actual'].max(), plot_df['Predicted'].max())
        fig.add_trace(go.Scatter(x=[min_val, max_val], 
                                  y=[min_val, max_val],
                                  mode='lines', name='Perfect Prediction', line=dict(dash='dash', color='#00D4AA')))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    # Feature Importance
    if best.get('feature_importance'):
        st.subheader("Feature Importance")
        imp_df = pd.DataFrame({
            'Feature': list(best['feature_importance'].keys()),
            'Importance': list(best['feature_importance'].values())
        }).sort_values('Importance', ascending=True)

        fig = px.bar(imp_df, x='Importance', y='Feature', orientation='h',
                    title="Feature Importance", template="plotly_dark",
                    color='Importance', color_continuous_scale='Teal')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    # Cross-validation scores
    st.subheader("Cross-Validation Scores")
    cv_data = []
    for name, result in results["models"].items():
        cv_data.append({"Model": name, "CV Mean": result["cv_mean"], "CV Std": result["cv_std"]})
    cv_df = pd.DataFrame(cv_data)

    fig = px.bar(cv_df, x="Model", y="CV Mean", error_y="CV Std",
                title="Cross-Validation Performance", template="plotly_dark",
                color="CV Mean", color_continuous_scale='Teal')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    # Export model
    st.subheader("Export Model")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("💾 Download Model (Joblib)", 
                          MLModeler.export_model(best, "joblib"),
                          f"{results['best_model']}_model.joblib",
                          use_container_width=True)
    with col2:
        st.download_button("📄 Download Model Info (JSON)",
                          MLModeler.export_model(best, "json"),
                          f"{results['best_model']}_info.json",
                          use_container_width=True)

# Split-View Comparison
with st.expander("⚖️ Model Comparison Dashboard", expanded=False):
    st.subheader("Model Comparison Dashboard")
    
    # Tabs for Supervised and Unsupervised comparison
    comparison_tabs = st.tabs(["Supervised Comparison", "Unsupervised Comparison"])
    
    with comparison_tabs[0]:  # Supervised Comparison
        render_section_header("Supervised Model Comparison", "Side-by-side model performance analysis")
        
        if SessionManager.get("supervised_models_trained"):
            results = SessionManager.get("supervised_models_trained")
            
            # Get model names
            model_names = list(results["models"].keys())
            
            if len(model_names) >= 2:
                col1, col2 = st.columns(2)
                with col1:
                    model_a = st.selectbox("Model A", model_names, key="model_a_comparison")
                with col2:
                    model_b = st.selectbox("Model B", [m for m in model_names if m != model_a], key="model_b_comparison_sup")
                
                # Get model results
                result_a = results["models"][model_a]
                result_b = results["models"][model_b]
                
                # Comparison metrics
                st.subheader(f"Comparing {model_a} vs {model_b}")
                
                if results['problem_type'] == 'classification':
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(f"{model_a} Accuracy", f"{result_a['metrics']['accuracy']:.4f}")
                        st.metric(f"{model_b} Accuracy", f"{result_b['metrics']['accuracy']:.4f}")
                        
                    with col2:
                        st.metric(f"{model_a} Precision", f"{result_a['metrics']['precision']:.4f}")
                        st.metric(f"{model_b} Precision", f"{result_b['metrics']['precision']:.4f}")
                        
                    with col3:
                        st.metric(f"{model_a} Recall", f"{result_a['metrics']['recall']:.4f}")
                        st.metric(f"{model_b} Recall", f"{result_b['metrics']['recall']:.4f}")
                        
                    with col4:
                        st.metric(f"{model_a} F1", f"{result_a['metrics']['f1']:.4f}")
                        st.metric(f"{model_b} F1", f"{result_b['metrics']['f1']:.4f}")
                
                else:  # regression
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(f"{model_a} R²", f"{result_a['metrics']['r2']:.4f}")
                        st.metric(f"{model_b} R²", f"{result_b['metrics']['r2']:.4f}")
                        
                    with col2:
                        st.metric(f"{model_a} RMSE", f"{result_a['metrics']['rmse']:.4f}")
                        st.metric(f"{model_b} RMSE", f"{result_b['metrics']['rmse']:.4f}")
                        
                    with col3:
                        st.metric(f"{model_a} MAE", f"{result_a['metrics']['mae']:.4f}")
                        st.metric(f"{model_b} MAE", f"{result_b['metrics']['mae']:.4f}")
                        
                    with col4:
                        st.metric(f"{model_a} MSE", f"{result_a['metrics']['mse']:.4f}")
                        st.metric(f"{model_b} MSE", f"{result_b['metrics']['mse']:.4f}")
                
                # Cross-validation comparison
                st.subheader("Cross-Validation Scores Comparison")
                comparison_df = pd.DataFrame({
                    'Model': [model_a, model_b],
                    'CV Mean': [result_a['cv_mean'], result_b['cv_mean']],
                    'CV Std': [result_a['cv_std'], result_b['cv_std']]
                })
                
                fig = px.bar(
                    comparison_df, 
                    x='Model', 
                    y='CV Mean', 
                    error_y='CV Std',
                    title="Cross-Validation Performance Comparison",
                    color='Model',
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Feature importance comparison if available
                if ('feature_importance' in result_a and result_a['feature_importance'] and 
                    'feature_importance' in result_b and result_b['feature_importance']):
                    
                    st.subheader("Feature Importance Comparison")
                    
                    # Get common features
                    features_a = set(result_a['feature_importance'].keys())
                    features_b = set(result_b['feature_importance'].keys())
                    common_features = features_a.intersection(features_b)
                    
                    if common_features:
                        importance_df = pd.DataFrame({
                            'Feature': list(common_features),
                            f'{model_a}': [result_a['feature_importance'][f] for f in common_features],
                            f'{model_b}': [result_b['feature_importance'][f] for f in common_features]
                        })
                        
                        # Melt for plotting
                        melted_df = importance_df.melt(id_vars=['Feature'], 
                                                       value_vars=[f'{model_a}', f'{model_b}'],
                                                       var_name='Model', 
                                                       value_name='Importance')
                        
                        fig = px.bar(
                            melted_df,
                            x='Feature',
                            y='Importance',
                            color='Model',
                            barmode='group',
                            title="Feature Importance Comparison"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Models have different features, unable to compare feature importance directly")
            else:
                st.info("Train at least 2 models to enable comparison")
        else:
            st.info("Train models in the main section to enable comparison")
    
    with comparison_tabs[1]:  # Unsupervised Comparison
        render_section_header("Unsupervised Method Comparison", "Compare different unsupervised learning techniques")
        
        st.info("Unsupervised comparison dashboard coming soon!")
        st.markdown("""
        This section will allow you to compare different unsupervised learning methods:
        - Compare clustering algorithms (K-Means, DBSCAN, Hierarchical, etc.)
        - Evaluate anomaly detection methods
        - Compare dimensionality reduction techniques
        - Visualize performance metrics for unsupervised tasks
        """)

with tab_unsupervised:
    # Unsupervised Learning Section
    st.header("Unsupervised Learning")
    
    # Problem Type Selection
    render_section_header("START HERE:", "Choose your problem type")
    
    unsup_problem_type = st.selectbox(
        "Select Unsupervised Learning Type", 
        ["Choose...", "Clustering", "Anomaly Detection", "Dimensionality Reduction", "Association/Pattern Mining"],
        format_func=lambda x: "Choose..." if x == "Choose..." else x,
        key="unsup_problem_type"
    )
    
    # Get numeric columns for all unsupervised tasks
    all_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if unsup_problem_type == "Clustering":
        # Clustering Section
        render_section_header("Clustering", "Group similar data points together")

        cluster_features = st.multiselect("Features for Clustering", all_numeric, 
                                           default=all_numeric[:min(3, len(all_numeric))],
                                           key="unsup_cluster_features")
        
        if cluster_features:  # Only proceed if features are selected
            col1, col2 = st.columns(2)
            with col1:
                cluster_algo = st.selectbox("Algorithm", ["K-Means", "DBSCAN", "Hierarchical", "Gaussian Mixture"], key="unsup_cluster_algo")
            with col2:
                if cluster_algo in ["K-Means", "Hierarchical", "Gaussian Mixture"]:
                    n_clusters = st.slider("Number of Clusters", 2, 10, 3, key="unsup_n_clusters")
                else:
                    n_clusters = None
            
            # Advanced clustering options
            with st.expander("Advanced Clustering Options"):
                if cluster_algo == "DBSCAN":
                    eps = st.slider("Epsilon (eps)", 0.1, 2.0, 0.5, key="dbscan_eps")
                    min_samples = st.slider("Minimum Samples", 1, 20, 5, key="dbscan_min_samples")
                else:
                    eps = 0.5
                    min_samples = 5
            
            if st.button("🎯 Run Clustering", type="primary", key="unsup_clustering_btn"):
                with st.spinner("Clustering..."):
                    cluster_result = MLModeler.cluster_data(df, cluster_features, algorithm=cluster_algo, 
                                                           n_clusters=n_clusters or 3, 
                                                           eps=eps, min_samples=min_samples)

                    # Store clustering results in a separate session state key
                    SessionManager.set("clustering_results", cluster_result)
                    
                    # Create visualizations
                    st.subheader(f"Clustering Results ({cluster_algo})")
                    
                    # Prepare data for visualization
                    pca_df = pd.DataFrame(cluster_result['pca_data'], columns=['PC1', 'PC2'])
                    pca_df['Cluster'] = cluster_result['labels'].astype(str)
                    
                    # Main scatter plot
                    fig = px.scatter(pca_df, x='PC1', y='PC2', color='Cluster',
                                    title="PCA Visualization of Clusters",
                                    template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold)
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Additional visualization: Cluster distribution
                    cluster_counts = pca_df['Cluster'].value_counts().sort_index()
                    cluster_viz = px.bar(x=cluster_counts.index, y=cluster_counts.values,
                                        title="Cluster Distribution",
                                        labels={'x': 'Cluster', 'y': 'Count'},
                                        template="plotly_dark")
                    cluster_viz.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(cluster_viz, use_container_width=True)
                    
                    st.info(f"Found {cluster_result['n_clusters']} clusters")
        else:
            st.warning("Please select at least one feature for clustering")
    
    elif unsup_problem_type == "Anomaly Detection":
        # Anomaly Detection Section
        render_section_header("Anomaly Detection", "Detect outliers in your data")
        
        anomaly_features = st.multiselect("Features for Anomaly Detection", all_numeric, 
                                         default=all_numeric[:min(3, len(all_numeric))],
                                         key="anomaly_features")
        
        if anomaly_features:  # Only proceed if features are selected
            col1, col2 = st.columns(2)
            with col1:
                anomaly_algorithm = st.selectbox("Anomaly Detection Algorithm", 
                                                ["Isolation Forest", "Local Outlier Factor", "One-Class SVM"],
                                                key="anomaly_algo")
            with col2:
                contamination = st.slider("Expected Contamination", 0.01, 0.5, 0.1, 
                                         help="The proportion of outliers in the dataset", key="contamination")
            
            if st.button("🔍 Detect Anomalies", key="detect_anomalies"):
                with st.spinner("Detecting anomalies..."):
                    try:
                        from sklearn.ensemble import IsolationForest
                        from sklearn.neighbors import LocalOutlierFactor
                        from sklearn.svm import OneClassSVM
                        
                        # Prepare data
                        X = df[anomaly_features].dropna()
                        scaler = StandardScaler()
                        X_scaled = scaler.fit_transform(X)
                        
                        # Apply selected algorithm
                        if anomaly_algorithm == "Isolation Forest":
                            model = IsolationForest(contamination=contamination, random_state=42)
                            outlier_labels = model.fit_predict(X_scaled)
                            outlier_labels = (outlier_labels == -1).astype(int)  # Convert to 0,1 format
                        elif anomaly_algorithm == "Local Outlier Factor":
                            model = LocalOutlierFactor(contamination=contamination, n_neighbors=min(20, len(X)-1))
                            outlier_labels = model.fit_predict(X_scaled)
                            outlier_labels = (outlier_labels == -1).astype(int)  # Convert to 0,1 format
                        else:  # One-Class SVM
                            model = OneClassSVM(nu=contamination)
                            outlier_labels = model.fit_predict(X_scaled)
                            outlier_labels = (outlier_labels == -1).astype(int)  # Convert to 0,1 format
                        
                        # Show results
                        num_anomalies = sum(outlier_labels)
                        st.metric("Number of Anomalies Detected", num_anomalies)
                        
                        # Add results to dataframe for visualization
                        vis_df = X.copy()
                        vis_df['is_anomaly'] = outlier_labels
                        
                        # Visualize anomalies
                        if len(anomaly_features) >= 2:
                            fig = px.scatter(vis_df, x=anomaly_features[0], y=anomaly_features[1], 
                                            color='is_anomaly', 
                                            title="Anomaly Detection Results",
                                            color_discrete_map={0: '#00D4AA', 1: '#FF4B4B'},
                                            template="plotly_dark")
                            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Additional visualization: Distribution of anomalies
                            anomaly_dist = px.histogram(vis_df, x=anomaly_features[0], color='is_anomaly',
                                                      title="Distribution of Anomalies in Selected Feature",
                                                      template="plotly_dark",
                                                      color_discrete_map={0: '#00D4AA', 1: '#FF4B4B'})
                            anomaly_dist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(anomaly_dist, use_container_width=True)
                        else:
                            st.warning("Need at least 2 features selected for visualization")
                            
                    except Exception as e:
                        st.error(f"Error during anomaly detection: {str(e)}")
        else:
            st.warning("Please select at least one feature for anomaly detection")
    
    elif unsup_problem_type == "Dimensionality Reduction":
        # Dimensionality Reduction Section
        render_section_header("Dimensionality Reduction", "Reduce data dimensions")
        
        dim_red_features = st.multiselect("Features for Dimensionality Reduction", all_numeric, 
                                         default=all_numeric[:min(5, len(all_numeric))],
                                         key="dim_red_features")
        
        if dim_red_features:  # Only proceed if features are selected
            # Check if UMAP is available
            umap_available = True
            try:
                import umap.umap_ as umap
            except ImportError:
                umap_available = False
            
            # Prepare the list of available methods
            available_methods = ["PCA", "t-SNE", "Truncated SVD", "Non-Negative Matrix Factorization"]
            if umap_available:
                available_methods.insert(2, "UMAP")  # Insert UMAP after t-SNE
            else:
                st.warning("UMAP is not installed. Install it with: pip install umap-learn to enable UMAP option.")
            
            reduction_method = st.selectbox("Dimensionality Reduction Method", 
                                           available_methods,
                                           key="reduction_method")
            
            n_components = st.slider("Number of Components", 2, min(10, len(dim_red_features)), 2,
                                    help="Number of dimensions to reduce to", key="n_components")
            
            if st.button("🔄 Perform Reduction", key="perform_reduction"):
                with st.spinner(f"Performing {reduction_method}..."):
                    try:
                        from sklearn.decomposition import PCA, TruncatedSVD, NMF
                        from sklearn.manifold import TSNE
                        
                        X = df[dim_red_features].dropna()
                        scaler = StandardScaler()
                        X_scaled = scaler.fit_transform(X)
                        
                        if reduction_method == "PCA":
                            reducer = PCA(n_components=n_components)
                            reduced_data = reducer.fit_transform(X_scaled)
                            explained_variance = reducer.explained_variance_ratio_.sum()
                            st.info(f"Explained variance ratio: {explained_variance:.2%}")
                        elif reduction_method == "t-SNE":
                            # t-SNE only works well with 2D or 3D
                            tsne_components = min(3, n_components)
                            reducer = TSNE(n_components=tsne_components, random_state=42)
                            reduced_data = reducer.fit_transform(X_scaled)
                        elif reduction_method == "UMAP":
                            reducer = umap.UMAP(n_components=n_components, random_state=24)
                            reduced_data = reducer.fit_transform(X_scaled)
                        elif reduction_method == "Truncated SVD":
                            reducer = TruncatedSVD(n_components=n_components, random_state=42)
                            reduced_data = reducer.fit_transform(X_scaled)
                        else:  # Non-Negative Matrix Factorization
                            reducer = NMF(n_components=n_components, random_state=42, max_iter=500)
                            reduced_data = reducer.fit_transform(X_scaled)
                        
                        # Create result dataframe
                        reduced_df = pd.DataFrame(
                            reduced_data, 
                            columns=[f'Dim_{i+1}' for i in range(reduced_data.shape[1])]
                        )
                        reduced_df['Index'] = X.index
                        
                        # Visualize
                        if n_components >= 2:
                            fig = px.scatter(reduced_df, x='Dim_1', y='Dim_2', 
                                            title=f"{reduction_method} Result",
                                            template="plotly_dark")
                            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Additional visualization: Explained variance if applicable
                            if reduction_method == "PCA":
                                exp_var_fig = px.bar(x=[f'PC{i+1}' for i in range(len(reducer.components_))], 
                                                     y=reducer.explained_variance_ratio_,
                                                     title="Explained Variance by Principal Component",
                                                     labels={'x': 'Principal Component', 'y': 'Explained Variance Ratio'},
                                                     template="plotly_dark")
                                exp_var_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(exp_var_fig, use_container_width=True)
                        
                        # Show the reduced data
                        st.subheader("Reduced Data Preview")
                        st.dataframe(reduced_df.head(100), use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Error during dimensionality reduction: {str(e)}")
        else:
            st.warning("Please select at least one feature for dimensionality reduction")
    
    elif unsup_problem_type == "Association/Pattern Mining":
        # Association Rule Mining Section
        render_section_header("Association Rule Mining", "Discover interesting relations between variables")
        
        st.info("Coming soon: Association rule mining for discovering interesting relations between variables in large databases.")
        
        # For now, we'll provide info about association mining
        st.markdown("""
        Association rule mining is a technique used to discover interesting relationships or patterns in large datasets.
        
        Common applications include:
        - Market basket analysis
        - Product recommendations
        - Cross-selling opportunities
        - Web usage mining
        
        Popular algorithms include:
        - Apriori Algorithm
        - FP-Growth Algorithm
        - Eclat Algorithm
        """)
        
        # Note: We would need to implement association rule mining algorithms
        # which are not part of sklearn but can be implemented using libraries like mlxtend
        st.warning("Association rule mining is not yet implemented in this version. You can use external libraries like mlxtend for this purpose.")