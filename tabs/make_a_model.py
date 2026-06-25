import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import time
import joblib
import psutil
import platform
from datetime import datetime
from io import StringIO
import logging
from typing import List, Tuple, Optional, Dict, Any
from scipy import stats


from scipy import stats
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
from sklearn.model_selection import learning_curve
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor,
    VotingClassifier, VotingRegressor,
)
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif, f_regression
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression, LinearRegression, Lasso, Ridge, ElasticNet
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.svm import SVC, SVR,LinearSVC,LinearSVR
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import (
    silhouette_score, calinski_harabasz_score, davies_bouldin_score,
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, r2_score, classification_report,
    mean_absolute_error, mean_squared_log_error
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import shared utilities and config
from utils import (
    model_key_to_estimator,
    build_preprocessor,
    generate_code_snippet,
    log_change,
    target_encode_column,
    get_numeric_columns,
    get_categorical_columns,
    get_datetime_columns,
    XGB_AVAILABLE, LGBM_AVAILABLE, CATBOOST_AVAILABLE,
    IMBLEARN_AVAILABLE, OPTUNA_AVAILABLE, SHAP_AVAILABLE
)
from config import BRAND_NAME, SECTION_HEADER_CLASS, SECTION_SUBHEADER_CLASS, N_JOBS

from sklearn.model_selection import (
    train_test_split, cross_val_score, StratifiedKFold, KFold,
    RandomizedSearchCV, validation_curve
)
from sklearn.pipeline import Pipeline
from sklearn.utils import resample

# Optional imports
try:
    import optuna
    from optuna.samplers import TPESampler
    OPTUNA_READY = True
except:
    OPTUNA_READY = False

try:
    from sklearnex import patch_sklearn
    patch_sklearn()
    INTEL_OPT = True
except:
    INTEL_OPT = False


def render_make_a_model_tab(filtered) -> None:
    """
    Unified Modeling Tab: Complete machine learning workflow for both supervised and unsupervised learning.
    """
    # Check if filtered data is None or empty
    # If it's a DatasetContext, check its filtered_df property
    if filtered is None:
        st.warning("⚠️ No data available. Please load or filter data first.")
        return
    
    # Check if it's a DatasetContext object and get the DataFrame
    if hasattr(filtered, 'filtered_df'):
        df_to_check = filtered.filtered_df
    else:
        df_to_check = filtered
    
    if df_to_check.empty:
        st.warning("⚠️ No data available. Please load or filter data first.")
        return

    # Handle both DataFrame and DatasetContext for work_df
    if hasattr(filtered, 'filtered_df'):
        st.session_state.work_df = filtered.filtered_df.copy()
    else:
        st.session_state.work_df = filtered.copy()

    st.markdown(f'<div class="{SECTION_HEADER_CLASS}">🧠 Make a Model Studio</div>', unsafe_allow_html=True)
    st.caption("Complete machine learning workflow: from data preparation to model deployment.")

    # --- Step 1: Learning Type Selection ---
    st.markdown("### 1️⃣ Learning Type Selection")
    _render_learning_type_selection()

    # Check if learning type is set
    if "learning_type" not in st.session_state:
        st.info("👆 Select learning type to continue.")
        return

    # --- Step 2: Problem Setup based on Learning Type ---
    if st.session_state.learning_type == "Supervised":
        st.markdown("### 2️⃣ Supervised Learning Setup")
        if hasattr(filtered, 'filtered_df'):
            _render_supervised_setup(filtered.filtered_df)
        else:
            _render_supervised_setup(filtered)
        
        # Only proceed if target and features are set
        if "target_col" not in st.session_state or st.session_state.target_col not in df_to_check.columns:
            st.info("👆 Select a target column to unlock advanced analysis.")
            return
            
        if "selected_features" not in st.session_state or not st.session_state.selected_features:
            st.info("👆 Select features to unlock advanced analysis.")
            return
    else:  # Unsupervised
        st.markdown("### 2️⃣ Unsupervised Learning Setup")
        if hasattr(filtered, 'filtered_df'):
            _render_unsupervised_setup(filtered.filtered_df)
        else:
            _render_unsupervised_setup(filtered)
        
        # Only proceed if features are selected
        if "selected_features" not in st.session_state or not st.session_state.selected_features:
            st.info("👆 Select features to unlock advanced analysis.")
            return

    # --- Step 3: Feature Engineering & Preprocessing ---
    st.markdown("### 3️⃣ Feature Engineering & Preprocessing")
    if hasattr(filtered, 'filtered_df'):
        _render_feature_engineering(filtered.filtered_df)
    else:
        _render_feature_engineering(filtered)
    
    # --- Step 4: Advanced Exploratory Data Analysis ---
    st.markdown("### 4️⃣ Advanced Exploratory Data Analysis")
    if hasattr(filtered, 'filtered_df'):
        _render_advanced_eda(filtered.filtered_df)
    else:
        _render_advanced_eda(filtered)

    # --- Step 5: Model Building & Evaluation ---
    st.markdown("### 5️⃣ Model Building & Evaluation")
    if hasattr(filtered, 'filtered_df'):
        _render_model_building(filtered.filtered_df)
    else:
        _render_model_building(filtered)

    # --- Step 6: Model Deployment ---
    st.markdown("### 6️⃣ Model Deployment")
    if hasattr(filtered, 'filtered_df'):
        _render_model_deployment(filtered.filtered_df)
    else:
        _render_model_deployment(filtered)


# =============== STEP 1: LEARNING TYPE SELECTION ===============
def _render_learning_type_selection() -> None:
    learning_type = st.radio(
        "Select learning type",
        ("Supervised", "Unsupervised"),
        help="Supervised: Predict a target variable. Unsupervised: Find patterns in data without a target."
    )
    st.session_state.learning_type = learning_type
    
    if learning_type == "Supervised":
        st.info("🎯 In supervised learning, you'll select a target variable to predict.")
    else:
        st.info("🔍 In unsupervised learning, you'll explore patterns in your data without a target variable.")


# =============== STEP 2: SUPERVISED SETUP ===============
def _render_supervised_setup(df: pd.DataFrame) -> None:
    col_options = list(df.columns)
    if not col_options:
        st.warning("No columns available.")
        return

    # Allow user to select both target and features
    targ = st.selectbox(
        "Select target column",
        options=col_options,
        index=len(col_options) - 1,
        help="Choose the column you want to predict"
    )
    st.session_state.target_col = targ

    # Feature selection - allow users to select features they want to work with
    available_features = [col for col in col_options if col != targ]
    selected_features = st.multiselect(
        "Select features to use in the model",
        options=available_features,
        default=available_features,
        help="Choose the features you want to use for training"
    )
    st.session_state.selected_features = selected_features

    # Analyze target
    series = df[targ]
    n_unique = series.nunique(dropna=True)
    dtype = str(series.dtype)
    total = len(series)

    # Smart problem type detection with confidence
    is_object = dtype in ['object', 'category', 'bool']
    ratio_unique = n_unique / total if total > 0 else 0

    if is_object or n_unique <= 10:
        suggested = "Classification"
        confidence = "High"
    elif ratio_unique < 0.02 and n_unique <= 50:
        suggested = "Classification"
        confidence = "Medium"
    else:
        suggested = "Regression"
        confidence = "High" if not is_object else "Low"

    st.markdown(f"""
    <div style="background:#f0f7ff; padding:12px; border-radius:8px; margin:10px 0;">
        <b>Target Analysis:</b> {n_unique} unique values | dtype: `{dtype}`<br>
        <b>Suggested Problem Type:</b> **{suggested}** (confidence: {confidence})
    </div>
    """, unsafe_allow_html=True)

    prob = st.radio(
        "Confirm problem type",
        ("Classification", "Regression"),
        index=0 if suggested == "Classification" else 1,
        help="Classification: predict categories. Regression: predict continuous values."
    )
    st.session_state.problem_type = prob

    # Business objective
    bg = st.selectbox(
        "Business objective",
        [
            "General purpose (balanced)",
            "Maximize accuracy",
            "High recall (minimize false negatives)",
            "High precision (minimize false positives)",
            "Interpretability over performance"
        ]
    )
    st.session_state.business_goal = bg

    # Cost matrix (classification only)
    if prob == "Classification":
        st.markdown("#### ⚖️ Cost Matrix (Optional)")
        col1, col2 = st.columns(2)
        with col1:
            fp_cost = st.number_input("Cost of False Positive", min_value=0.0, value=1.0, step=0.1)
        with col2:
            fn_cost = st.number_input("Cost of False Negative", min_value=0.0, value=2.0, step=0.1)
        st.session_state.model_cost = {'fp': fp_cost, 'fn': fn_cost}
    else:
        st.session_state.model_cost = None

    # Date expansion
    date_cols = get_datetime_columns(df)
    if date_cols:
        st.markdown("#### 📅 Date Feature Expansion")
        add_dates = st.multiselect("Expand date columns into features", date_cols)
        if st.button("Apply Date Expansion", type="secondary"):
            for c in add_dates:
                st.session_state.work_df = date_feature_engineer(st.session_state.work_df, c)
            # Invalidate cached filtered view and health score after modifying working dataset
            st.session_state['filtered_data'] = None
            st.session_state['cached_data_health'] = None
            st.success("✅ Date features added!")
            log_change("Expanded date features", str(add_dates))
            st.rerun()

    if st.button("✅ Confirm Target & Features", type="primary"):
        if selected_features:
            st.success("Target and features confirmed. Advanced analysis unlocked.")
            log_change("Confirmed target and features", f"Target: {targ}, Features: {selected_features}, Type: {prob}")
        else:
            st.warning("Please select at least one feature to continue.")


# =============== STEP 2: UNSUPERVISED SETUP ===============
def _render_unsupervised_setup(df: pd.DataFrame) -> None:
    col_options = list(df.columns)
    if not col_options:
        st.warning("No columns available.")
        return

    # Feature selection
    selected_features = st.multiselect(
        "Select features for analysis",
        options=col_options,
        default=col_options,
        help="Choose the columns you want to use for unsupervised learning"
    )
    st.session_state.selected_features = selected_features
    
    # Problem type for unsupervised learning
    unsupervised_type = st.selectbox(
        "Select unsupervised learning task",
        ("Clustering", "Dimensionality Reduction", "Anomaly Detection"),
        help="Clustering: Group similar data points. Dimensionality Reduction: Reduce number of features. Anomaly Detection: Find outliers."
    )
    st.session_state.unsupervised_task = unsupervised_type
    
    # Clustering specific options
    if unsupervised_type == "Clustering":
        n_clusters = st.slider("Number of clusters", 2, 20, 3)
        st.session_state.n_clusters = n_clusters
        
        clustering_algo = st.selectbox(
            "Clustering algorithm",
            ("K-Means", "DBSCAN"),
            index=0
        )
        st.session_state.clustering_algo = clustering_algo

    if st.button("✅ Confirm Features & Proceed", type="primary") and selected_features:
        st.success("Features confirmed. Advanced analysis unlocked.")
        log_change("Confirmed features", f"Features: {selected_features}, Task: {unsupervised_type}")


# =============== STEP 3: ADVANCED EDA ===============
def _render_advanced_eda(df: pd.DataFrame) -> None:
    if st.session_state.learning_type == "Supervised":
        _render_supervised_eda(df)
    else:
        _render_unsupervised_eda(df)


def _render_supervised_eda(df: pd.DataFrame) -> None:
    target = st.session_state.target_col
    ptype = st.session_state.problem_type
    X = df.drop(columns=[target])
    y = df[target]

    tabs = st.tabs([
        "📊 Target Distribution",
        "📈 Feature Summaries",
        "🔗 Feature-Target Relationships",
        "⚠️ Data Quality & Risks",
        "🔍 Feature Importance"
    ])

    # --- Tab 1: Target Distribution ---
    with tabs[0]:
        if ptype == "Classification":
            vc = y.value_counts(dropna=False).reset_index()
            vc.columns = [target, 'count']
            fig = px.bar(vc, x=target, y='count', text='count', title="Class Distribution")
            st.plotly_chart(fig, use_container_width=True)
            if len(vc) > 2:
                st.info("💡 Multi-class detected. Consider stratified sampling during train/test split.")
        else:
            fig = px.histogram(df, x=target, nbins=40, title="Target Distribution", marginal="box")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(y.describe().to_frame().T, use_container_width=True)

    # --- Tab 2: Feature Summaries ---
    with tabs[1]:
        num_cols = get_numeric_columns(X)
        cat_cols = get_categorical_columns(X)

        if num_cols:
            st.subheader("Numeric Features")
            st.dataframe(X[num_cols].describe().T, use_container_width=True)
        if cat_cols:
            st.subheader("Categorical Features (Top 10 Levels)")
            for c in cat_cols[:6]:
                st.write(f"**{c}**")
                st.dataframe(X[c].astype(str).value_counts().head(10).to_frame("count"), use_container_width=True)

    # --- Tab 3: Feature-Target Relationships ---
    with tabs[2]:
        num_cols = get_numeric_columns(X)
        if ptype == "Classification" and num_cols:
            st.subheader("Numeric Features vs Target (Box Plots)")
            cols_to_plot = num_cols[:6]  # Limit for performance
            for i in range(0, len(cols_to_plot), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols_to_plot[i:i+2]):
                    with cols[j]:
                        fig = px.box(df, x=target, y=col, title=f"{col} by {target}")
                        st.plotly_chart(fig, use_container_width=True)
        elif ptype == "Regression" and num_cols:
            st.subheader("Top Correlations with Target")
            corr_with_target = df[num_cols + [target]].corr()[target].drop(target).abs().sort_values(ascending=False)
            top3 = corr_with_target.head(3).index.tolist()
            for col in top3:
                fig = px.scatter(df, x=col, y=target, trendline="ols", title=f"{target} vs {col} (r={corr_with_target[col]:.2f})")
                st.plotly_chart(fig, use_container_width=True)

    # --- Tab 4: Data Quality & Risks ---
    with tabs[3]:
        # Missingness
        miss = df.isnull().sum()
        miss = miss[miss > 0].sort_values(ascending=False)
        if not miss.empty:
            miss_df = miss.reset_index()
            miss_df.columns = ['column', 'missing_count']
            miss_df['missing_pct'] = (miss_df['missing_count'] / len(df)) * 100
            fig = px.bar(miss_df, x='column', y='missing_count', hover_data=['missing_pct'], title='Missing Values')
            st.plotly_chart(fig, use_container_width=True)

        # High cardinality
        high_card = detect_high_cardinality(df, threshold=50)
        if high_card:
            st.warning("⚠️ **High Cardinality Features Detected**")
            for col, n in high_card:
                st.write(f"- `{col}`: {n} unique values → consider binning or target encoding")

        # Duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            st.warning(f"⚠️ **{dup_count:,} duplicate rows** detected — may cause overfitting.")

        # Multicollinearity
        num_cols = get_numeric_columns(df)
        if len(num_cols) >= 2:
            corr = df[num_cols].corr().abs()
            upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
            high_corr_pairs = [(i, j, upper.iloc[i,j]) for i in range(upper.shape[0]) for j in range(upper.shape[1]) if upper.iloc[i,j] > 0.9]
            if high_corr_pairs:
                st.error("🔴 **High Multicollinearity Detected** (|r| > 0.9)")
                for i, j, v in high_corr_pairs[:5]:
                    st.write(f"- `{num_cols[i]}` ↔ `{num_cols[j]}`: {v:.2f}")

        # Data leakage warning
        target_lower = target.lower()
        if any(keyword in target_lower for keyword in ['future', 'next', 'predict', 'forecast']):
            st.warning("⚠️ **Potential Data Leakage**: Target variable appears to contain future information. "
                      "Ensure you're not using future data to predict future outcomes.")
        
        # Outliers detection for numeric features
        if num_cols:
            st.subheader("Outliers Detection")
            outliers_info = []
            for col in num_cols[:10]:  # Limit to first 10 for performance
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                if len(outliers) > 0:
                    outliers_info.append((col, len(outliers), len(outliers)/len(df)*100))
            
            if outliers_info:
                outliers_df = pd.DataFrame(outliers_info, columns=['Feature', 'Outliers Count', 'Percentage'])
                st.dataframe(outliers_df.style.format({"Percentage": "{:.2f}%"}), use_container_width=True)
            else:
                st.info("✅ No significant outliers detected in numeric features.")

    # --- Tab 5: Feature Importance ---
    with tabs[4]:
        st.subheader("Feature Importance Analysis")
        num_cols = get_numeric_columns(X)
        cat_cols = get_categorical_columns(X)
        
        # Prepare data for mutual information
        X_encoded = X.copy()
        for col in cat_cols:
            if X_encoded[col].dtype == 'object':
                le = LabelEncoder()
                X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
        
        try:
            if ptype == "Classification":
                # For classification, we need to encode the target if it's not numeric
                y_encoded = y.copy()
                if y.dtype == 'object':
                    le = LabelEncoder()
                    y_encoded = le.fit_transform(y.astype(str))
                
                mi_scores = mutual_info_classif(X_encoded, y_encoded, random_state=42)
            else:
                mi_scores = mutual_info_regression(X_encoded, y, random_state=42)
            
            # Create feature importance dataframe
            feature_importance = pd.DataFrame({
                'feature': X_encoded.columns,
                'mutual_info': mi_scores
            }).sort_values('mutual_info', ascending=False)
            
            # Plot top 15 features
            top_features = feature_importance.head(15)
            fig = px.bar(top_features, x='mutual_info', y='feature', orientation='h',
                        title='Top 15 Features by Mutual Information')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(feature_importance.style.format({"mutual_info": "{:.4f}"}), use_container_width=True)
            
            # Provide recommendations based on feature importance
            low_importance_features = feature_importance[feature_importance['mutual_info'] < 0.01]
            if len(low_importance_features) > 0:
                st.info(f"💡 Found {len(low_importance_features)} features with very low mutual information (<0.01). "
                        "Consider removing these features to reduce dimensionality.")
                
        except Exception as e:
            st.warning(f"⚠️ Could not compute feature importance: {str(e)}")
            logger.warning(f"Feature importance computation failed: {e}")


def _render_unsupervised_eda(df: pd.DataFrame) -> None:
    selected_features = st.session_state.selected_features
    task = st.session_state.unsupervised_task
    
    # Filter dataframe to selected features
    df_filtered = df[selected_features]
    
    tabs = st.tabs([
        "📊 Data Distribution",
        "📈 Feature Summaries",
        "🔗 Feature Relationships",
        "⚠️ Data Quality & Risks"
    ])

    # --- Tab 1: Data Distribution ---
    with tabs[0]:
        num_cols = get_numeric_columns(df_filtered)
        cat_cols = get_categorical_columns(df_filtered)
        
        if num_cols:
            st.subheader("Numeric Features Distribution")
            for col in num_cols[:6]:  # Limit for performance
                fig = px.histogram(df_filtered, x=col, nbins=30, title=f"Distribution of {col}")
                st.plotly_chart(fig, use_container_width=True)
        
        if cat_cols:
            st.subheader("Categorical Features Distribution")
            for col in cat_cols[:6]:  # Limit for performance
                vc = df_filtered[col].value_counts().head(10).reset_index()
                vc.columns = [col, 'count']
                fig = px.bar(vc, x=col, y='count', text='count', title=f"Distribution of {col}")
                st.plotly_chart(fig, use_container_width=True)

    # --- Tab 2: Feature Summaries ---
    with tabs[1]:
        num_cols = get_numeric_columns(df_filtered)
        cat_cols = get_categorical_columns(df_filtered)

        if num_cols:
            st.subheader("Numeric Features")
            st.dataframe(df_filtered[num_cols].describe().T, use_container_width=True)
        if cat_cols:
            st.subheader("Categorical Features (Top 10 Levels)")
            for c in cat_cols[:6]:
                st.write(f"**{c}**")
                st.dataframe(df_filtered[c].astype(str).value_counts().head(10).to_frame("count"), use_container_width=True)

    # --- Tab 3: Feature Relationships ---
    with tabs[2]:
        num_cols = get_numeric_columns(df_filtered)
        if len(num_cols) >= 2:
            st.subheader("Correlation Matrix")
            corr = df_filtered[num_cols].corr()
            fig = px.imshow(corr, text_auto=True, aspect="auto", 
                           title="Feature Correlation Matrix")
            st.plotly_chart(fig, use_container_width=True)
            
            # Scatter plots for top correlated pairs
            st.subheader("Top Feature Relationships")
            corr_flat = corr.abs().unstack().sort_values(ascending=False)
            # Remove self-correlations (diagonal)
            corr_flat = corr_flat[corr_flat != 1.0]
            top_pairs = corr_flat.head(3)
            
            for (feat1, feat2), corr_val in top_pairs.items():
                fig = px.scatter(df_filtered, x=feat1, y=feat2, 
                                title=f"{feat1} vs {feat2} (r={corr_val:.2f})")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need at least 2 numeric features to show relationships.")

    # --- Tab 4: Data Quality & Risks ---
    with tabs[3]:
        # Missingness
        miss = df_filtered.isnull().sum()
        miss = miss[miss > 0].sort_values(ascending=False)
        if not miss.empty:
            miss_df = miss.reset_index()
            miss_df.columns = ['column', 'missing_count']
            miss_df['missing_pct'] = (miss_df['missing_count'] / len(df_filtered)) * 100
            fig = px.bar(miss_df, x='column', y='missing_count', hover_data=['missing_pct'], title='Missing Values')
            st.plotly_chart(fig, use_container_width=True)

        # High cardinality
        high_card = detect_high_cardinality(df_filtered, threshold=50)
        if high_card:
            st.warning("⚠️ **High Cardinality Features Detected**")
            for col, n in high_card:
                st.write(f"- `{col}`: {n} unique values → consider binning or encoding")

        # Duplicates
        dup_count = df_filtered.duplicated().sum()
        if dup_count > 0:
            st.warning(f"⚠️ **{dup_count:,} duplicate rows** detected — may affect clustering.")

        # Outliers detection for numeric features
        if num_cols:
            st.subheader("Outliers Detection")
            outliers_info = []
            for col in num_cols[:10]:  # Limit to first 10 for performance
                Q1 = df_filtered[col].quantile(0.25)
                Q3 = df_filtered[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = df_filtered[(df_filtered[col] < lower_bound) | (df_filtered[col] > upper_bound)]
                if len(outliers) > 0:
                    outliers_info.append((col, len(outliers), len(outliers)/len(df_filtered)*100))
            
            if outliers_info:
                outliers_df = pd.DataFrame(outliers_info, columns=['Feature', 'Outliers Count', 'Percentage'])
                st.dataframe(outliers_df.style.format({"Percentage": "{:.2f}%"}), use_container_width=True)
            else:
                st.info("✅ No significant outliers detected in numeric features.")


# =============== STEP 4: FEATURE ENGINEERING ===============
def _render_feature_engineering(df: pd.DataFrame) -> None:
    if st.session_state.learning_type == "Supervised":
        _render_supervised_feature_engineering(df)
    else:
        _render_unsupervised_feature_engineering(df)


def _render_supervised_feature_engineering(df: pd.DataFrame) -> None:
    st.markdown("### Feature Engineering for Supervised Learning")
    
    # Feature selection options
    st.subheader("Feature Selection")
    feature_selection_method = st.selectbox(
        "Select feature selection method",
        ("No Selection", "Based on Mutual Information", "Manual Selection", "Variance Threshold", "Correlation-based")
    )
    
    target = st.session_state.target_col
    ptype = st.session_state.problem_type
    
    if feature_selection_method == "Based on Mutual Information":
        X = df[st.session_state.selected_features]
        y = df[target]
        
        # Calculate mutual information
        num_cols = get_numeric_columns(X)
        cat_cols = get_categorical_columns(X)
        
        X_encoded = X.copy()
        for col in cat_cols:
            if X_encoded[col].dtype == 'object':
                le = LabelEncoder()
                X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
        
        try:
            if ptype == "Classification":
                y_encoded = y.copy()
                if y.dtype == 'object':
                    le = LabelEncoder()
                    y_encoded = le.fit_transform(y.astype(str))
                mi_scores = mutual_info_classif(X_encoded, y_encoded, random_state=42)
            else:
                mi_scores = mutual_info_regression(X_encoded, y, random_state=42)
            
            feature_importance = pd.DataFrame({
                'feature': X_encoded.columns,
                'mutual_info': mi_scores
            }).sort_values('mutual_info', ascending=False)
            
            n_features = st.slider("Select top N features", 1, len(feature_importance), min(10, len(feature_importance)))
            top_features = feature_importance.head(n_features)['feature'].tolist()
            st.session_state.selected_features = top_features
            st.success(f"Selected top {n_features} features based on mutual information")
            
            # Visualization of feature importance
            st.subheader("Feature Importance Visualization")
            fig = px.bar(feature_importance.head(n_features), x='mutual_info', y='feature', orientation='h',
                        title='Top Feature Importances (Mutual Information)')
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning(f"⚠️ Could not perform feature selection: {str(e)}")
    
    elif feature_selection_method == "Manual Selection":
        target = st.session_state.target_col
        available_features = [col for col in df.columns if col != target]
        selected_features = st.multiselect("Select features to use", available_features, default=st.session_state.selected_features)
        st.session_state.selected_features = selected_features
    
    elif feature_selection_method == "Variance Threshold":
        X = df[st.session_state.selected_features]
        num_cols = get_numeric_columns(X)
        if num_cols:
            variance_threshold = st.slider("Variance threshold", 0.0, 1.0, 0.01)
            # This is a simplified approach - in practice, you'd use sklearn.feature_selection.VarianceThreshold
            variances = X[num_cols].var()
            selected_by_variance = variances[variances > variance_threshold].index.tolist()
            st.session_state.selected_features = selected_by_variance
            st.success(f"Selected {len(selected_by_variance)} features based on variance threshold")
            
            # Visualization of feature variance
            st.subheader("Feature Variance Visualization")
            fig = px.bar(variances.reset_index(), x='index', y=0, title='Feature Variances')
            fig.update_layout(xaxis_title="Features", yaxis_title="Variance")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No numeric features available for variance-based selection")
    
    elif feature_selection_method == "Correlation-based":
        X = df[st.session_state.selected_features]
        num_cols = get_numeric_columns(X)
        if len(num_cols) >= 2:
            correlation_threshold = st.slider("Correlation threshold", 0.0, 1.0, 0.8)
            corr = X[num_cols].corr().abs()
            upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
            high_corr_features = [col for col in upper.columns if any(upper[col] > correlation_threshold)]
            st.session_state.selected_features = [col for col in st.session_state.selected_features if col not in high_corr_features or col not in num_cols]
            st.success(f"Removed {len(high_corr_features)} highly correlated features")
            
            # Visualization of correlation matrix
            st.subheader("Correlation Matrix")
            fig = px.imshow(corr, text_auto=True, aspect="auto", title="Feature Correlation Matrix")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Need at least 2 numeric features for correlation-based selection")
    
    else:
        # Use all features except target
        target = st.session_state.target_col
        st.session_state.selected_features = [col for col in df.columns if col != target]
    
    # Advanced feature creation
    st.subheader("Feature Creation")
    feature_creation_option = st.selectbox(
        "Select feature creation method",
        ("None", "Polynomial Features", "Log Transformations", "Custom Feature Creation")
    )
    
    if feature_creation_option == "Polynomial Features":
        poly_degree = st.slider("Polynomial degree", 2, 3, 2)
        st.session_state.poly_degree = poly_degree
        st.info(f"Will create polynomial features of degree {poly_degree}")
    
    elif feature_creation_option == "Log Transformations":
        X = df[st.session_state.selected_features]
        num_cols = get_numeric_columns(X)
        log_transform_features = st.multiselect("Select features for log transformation", num_cols)
        st.session_state.log_transform_features = log_transform_features
        st.info(f"Will apply log transformation to {len(log_transform_features)} features")
    
    elif feature_creation_option == "Custom Feature Creation":
        st.info("Custom feature creation will be applied during preprocessing")
        st.session_state.custom_features = True
    
    # Encoding options
    st.subheader("Encoding Options")
    cat_cols = get_categorical_columns(df[st.session_state.selected_features])
    if cat_cols:
        encoding_method = st.selectbox(
            "Select encoding method for categorical features",
            ("One-Hot Encoding", "Label Encoding", "Target Encoding", "Frequency Encoding")
        )
        st.session_state.encoding_method = encoding_method
        
        if encoding_method == "Target Encoding":
            smoothing = st.slider("Target encoding smoothing", 0.0, 10.0, 1.0)
            st.session_state.target_encoding_smoothing = smoothing
    else:
        st.info("No categorical features found. No encoding needed.")
        st.session_state.encoding_method = "None"
    
    # Scaling options
    st.subheader("Scaling Options")
    num_cols = get_numeric_columns(df[st.session_state.selected_features])
    if num_cols:
        scaling_method = st.selectbox(
            "Select scaling method for numeric features",
            ("No Scaling", "Standard Scaling (Z-score)", "Min-Max Scaling", "Robust Scaling", "MaxAbs Scaling")
        )
        st.session_state.scaling_method = scaling_method
        
        if scaling_method != "No Scaling":
            outlier_handling = st.checkbox("Handle outliers before scaling", value=False)
            st.session_state.outlier_handling = outlier_handling
    else:
        st.info("No numeric features found. No scaling needed.")
        st.session_state.scaling_method = "None"
    
    # Missing value handling
    st.subheader("Missing Value Handling")
    missing_value_strategy = st.selectbox(
        "How to handle missing values",
        ("Default (auto-detect)", "Drop rows with missing values", "Mean imputation", "Median imputation", "Mode imputation", "Constant value")
    )
    st.session_state.missing_value_strategy = missing_value_strategy
    
    if missing_value_strategy == "Constant value":
        constant_value = st.text_input("Enter constant value for missing data", "0")
        st.session_state.missing_constant_value = constant_value
    
    if st.button("Apply Feature Engineering"):
        st.success("Feature engineering settings applied!")
        log_change("Applied feature engineering", f"Selection: {feature_selection_method}, Creation: {feature_creation_option}, Encoding: {st.session_state.encoding_method}, Scaling: {st.session_state.scaling_method}")


def _render_unsupervised_feature_engineering(df: pd.DataFrame) -> None:
    st.markdown("### Feature Engineering for Unsupervised Learning")
    
    selected_features = st.session_state.selected_features
    df_filtered = df[selected_features]
    
    # Feature selection options
    st.subheader("Feature Selection")
    feature_selection_method = st.selectbox(
        "Select feature selection method",
        ("No Selection", "Variance Threshold", "Manual Selection")
    )
    
    if feature_selection_method == "Variance Threshold":
        num_cols = get_numeric_columns(df_filtered)
        if num_cols:
            variance_threshold = st.slider("Variance threshold", 0.0, 1.0, 0.01)
            # This is a simplified approach - in practice, you'd use sklearn.feature_selection.VarianceThreshold
            variances = df_filtered[num_cols].var()
            selected_by_variance = variances[variances > variance_threshold].index.tolist()
            st.session_state.selected_features = selected_by_variance
            st.success(f"Selected {len(selected_by_variance)} features based on variance threshold")
        else:
            st.warning("No numeric features available for variance-based selection")
    
    elif feature_selection_method == "Manual Selection":
        selected_features = st.multiselect("Select features to use", selected_features, default=selected_features)
        st.session_state.selected_features = selected_features
    
    # Encoding options
    st.subheader("Encoding Options")
    cat_cols = get_categorical_columns(df_filtered)
    if cat_cols:
        encoding_method = st.selectbox(
            "Select encoding method for categorical features",
            ("One-Hot Encoding", "Label Encoding")
        )
        st.session_state.encoding_method = encoding_method
    else:
        st.info("No categorical features found. No encoding needed.")
        st.session_state.encoding_method = "None"
    
    # Scaling options
    st.subheader("Scaling Options")
    num_cols = get_numeric_columns(df_filtered)
    if num_cols:
        scaling_method = st.selectbox(
            "Select scaling method for numeric features",
            ("No Scaling", "Standard Scaling (Z-score)", "Min-Max Scaling", "Robust Scaling")
        )
        st.session_state.scaling_method = scaling_method
    else:
        st.info("No numeric features found. No scaling needed.")
        st.session_state.scaling_method = "None"
    
    # Dimensionality reduction for clustering
    if st.session_state.unsupervised_task == "Clustering":
        st.subheader("Dimensionality Reduction")
        apply_pca = st.checkbox("Apply PCA for dimensionality reduction")
        if apply_pca:
            n_components = st.slider("Number of components", 2, min(20, len(num_cols)+len(cat_cols)), 2)
            st.session_state.apply_pca = True
            st.session_state.pca_components = n_components
        else:
            st.session_state.apply_pca = False
    
    if st.button("Apply Feature Engineering"):
        st.success("Feature engineering settings applied!")
        log_change("Applied feature engineering", f"Selection: {feature_selection_method}, Encoding: {st.session_state.encoding_method}, Scaling: {st.session_state.scaling_method}")


# =============== STEP 5: MODEL BUILDING & EVALUATION ===============
def _render_model_building(df: pd.DataFrame) -> None:
    if st.session_state.learning_type == "Supervised":
        _render_supervised_model_building(df)
    else:
        _render_unsupervised_model_building(df)


def _render_supervised_model_building(df: pd.DataFrame) -> None:
    target = st.session_state.target_col
    ptype = st.session_state.problem_type
    selected_features = st.session_state.selected_features if 'selected_features' in st.session_state else [col for col in df.columns if col != target]
    
    tabs = st.tabs([
        "🏆 Model Selection",
        "⚡ Quick Train",
        "📊 Model Evaluation",
        "⚙️ Hyperparameter Tuning"
    ])
    
    with tabs[0]:
        _render_model_selection(df)
    
    with tabs[1]:
        _render_quick_train(df)
    
    with tabs[2]:
        _render_model_evaluation(df)
    
    with tabs[3]:
        _render_advanced_tuning(df)


def _render_model_selection(df: pd.DataFrame) -> None:
    target = st.session_state.target_col
    ptype = st.session_state.problem_type
    n = len(df)

    # Hardware-aware recommendations
    cpu_count = psutil.cpu_count(logical=True)
    memory_gb = psutil.virtual_memory().total / (1024**3)
    st.info(f"**System**: {cpu_count} CPUs · {memory_gb:.1f} GB RAM · {'Intel Optimizations: ON' if INTEL_OPT else 'Standard'}")

    # Model pool
    base_models = ["RandomForest", "LogisticRegression", "KNN", "NaiveBayes"] if ptype == "Classification" else ["RandomForestReg", "LinearRegression", "KNN"]
    boosters = []
    if XGB_AVAILABLE: boosters.append("XGBoost" if ptype == "Classification" else "XGBoostReg")
    if LGBM_AVAILABLE: boosters.append("LightGBM" if ptype == "Classification" else "LightGBMReg")
    if CATBOOST_AVAILABLE: boosters.append("CatBoost" if ptype == "Classification" else "CatBoostReg")

    all_models = base_models + boosters

    st.markdown("### 🏁 Cross-Validation Leaderboard")
    chosen = st.multiselect("Select models to benchmark", all_models, default=all_models[:3])
    cv_folds = st.slider("CV folds", 3, 10, min(5, max(3, n//100)), 1)
    
    # Multiple metrics selection
    if ptype == "Classification":
        scoring_options = ["accuracy", "f1_weighted", "precision_weighted", "recall_weighted", "roc_auc"]
    else:
        scoring_options = ["r2", "neg_root_mean_squared_error", "neg_mean_absolute_error"]
    
    scoring = st.multiselect("Metrics to evaluate", scoring_options, default=scoring_options[0])
    
    # Option to use stratified sampling
    use_stratified = st.checkbox("Use stratified sampling", value=True)

    if st.button("🚀 Run Leaderboard", type="primary"):
        X = df.drop(columns=[target])
        y = df[target]
        if ptype == "Classification" and y.dtype == object:
            y = pd.factorize(y)[0]

        # Auto-select encoding
        cat_cols = get_categorical_columns(X)
        total_card = sum(X[c].nunique() for c in cat_cols) if len(cat_cols) > 0 else 0
        enc_strategy = "onehot" if total_card < 200 else "ordinal"

        leaderboard = []
        progress = st.progress(0)
        total_tasks = len(chosen) * len(scoring)
        task_count = 0
        
        for i, model_name in enumerate(chosen):
            try:
                preproc, _, _, _ = build_preprocessor(df, target, encoding_strategy=enc_strategy)
                model = model_key_to_estimator(model_name, ptype)
                pipe = Pipeline([('preproc', preproc), ('model', model)])

                cv = StratifiedKFold(cv_folds, shuffle=True, random_state=42) if ptype == "Classification" and use_stratified else KFold(cv_folds, shuffle=True, random_state=42)
                
                # Evaluate multiple metrics
                model_results = {'Model': model_name}
                for metric in scoring:
                    try:
                        scores = cross_val_score(pipe, X, y, cv=cv, scoring=metric, n_jobs=N_JOBS)
                        model_results[f'{metric}_mean'] = float(scores.mean())
                        model_results[f'{metric}_std'] = float(scores.std())
                    except Exception as e:
                        model_results[f'{metric}_mean'] = np.nan
                        model_results[f'{metric}_std'] = np.nan
                    
                    task_count += 1
                    progress.progress(task_count / total_tasks)
                
                leaderboard.append(model_results)
            except Exception as e:
                st.warning(f"⚠️ {model_name} failed: {str(e)[:100]}")
                task_count += len(scoring)
                progress.progress(task_count / total_tasks)

        if leaderboard:
            lb_df = pd.DataFrame(leaderboard)
            # Sort by first metric
            first_metric = scoring[0]
            lb_df = lb_df.sort_values(f'{first_metric}_mean', ascending=False).reset_index(drop=True)
            st.session_state.leaderboard = lb_df
            
            # Display results with better formatting
            display_columns = ['Model'] + [f'{metric}_mean' for metric in scoring]
            st.dataframe(lb_df[display_columns].style.format({f'{metric}_mean': "{:.4f}" for metric in scoring}), use_container_width=True)
            
            best = lb_df.iloc[0]
            st.success(f"🏆 **{best['Model']}** is the top performer (Mean {first_metric}: **{best[f'{first_metric}_mean']:.4f}**)")
            
            # Visualization of results
            if len(scoring) > 1:
                st.subheader("Model Comparison Across Metrics")
                fig_df = lb_df.melt(id_vars=['Model'], 
                                   value_vars=[f'{metric}_mean' for metric in scoring],
                                   var_name='Metric', 
                                   value_name='Score')
                fig_df['Metric'] = fig_df['Metric'].str.replace('_mean', '')
                fig = px.bar(fig_df, x='Model', y='Score', color='Metric', barmode='group',
                            title='Model Performance Comparison')
                st.plotly_chart(fig, use_container_width=True)

        progress.empty()


def _render_quick_train(df: pd.DataFrame) -> None:
    target = st.session_state.target_col
    ptype = st.session_state.problem_type

    # Model selection
    lb = st.session_state.get("leaderboard")
    default_model = lb.iloc[0]['Model'] if lb is not None and not lb.empty else ("RandomForest" if ptype == "Classification" else "RandomForestReg")
    
    # Available models based on problem type
    model_options = []
    if ptype == "Classification":
        model_options = ["RandomForest", "LogisticRegression", "KNN", "NaiveBayes"]
        if XGB_AVAILABLE: model_options.append("XGBoost")
        if LGBM_AVAILABLE: model_options.append("LightGBM")
        if CATBOOST_AVAILABLE: model_options.append("CatBoost")
    else:  # Regression
        model_options = ["RandomForestReg", "LinearRegression", "KNN"]
        if XGB_AVAILABLE: model_options.append("XGBoostReg")
        if LGBM_AVAILABLE: model_options.append("LightGBMReg")
        if CATBOOST_AVAILABLE: model_options.append("CatBoostReg")

    model_choice = st.selectbox("Model to train", model_options, index=0)

    # Train/test split
    test_frac = st.slider("Test fraction", 0.1, 0.4, 0.2)
    sampling = st.selectbox("Class balancing", ["None", "SMOTE", "Random Undersample"]) if ptype == "Classification" else "None"

    # Feature engineering
    st.markdown("### 🛠️ Feature Engineering")
    enc_strategy = st.radio("Categorical encoding", ["onehot", "ordinal", "target_encoding"], index=0)
    poly_degree = st.slider("Polynomial degree", 1, 3, 1)
    include_interactions = st.checkbox("Include interactions", value=False)

    if st.button("🎯 Train & Evaluate Model", type="primary"):
        X = df.drop(columns=[target])
        y = df[target]
        if ptype == "Classification" and y.dtype == object:
            y = pd.factorize(y)[0]

        # Target encoding
        te_cols = []
        if enc_strategy == "target_encoding" and ptype == "Regression":
            cat_cols = get_categorical_columns(X)
            for c in sorted(cat_cols, key=lambda x: X[x].nunique(), reverse=True)[:5]:
                try:
                    X[c] = target_encode_column(X[c], df[target])
                    te_cols.append(c)
                except:
                    pass

        # Handle class imbalance
        if ptype == "Classification" and sampling != "None" and IMBLEARN_AVAILABLE:
            try:
                if sampling == "SMOTE":
                    from imblearn.over_sampling import SMOTE
                    smote = SMOTE(random_state=42)
                    X, y = smote.fit_resample(X, y)
                elif sampling == "Random Undersample":
                    from imblearn.under_sampling import RandomUnderSampler
                    rus = RandomUnderSampler(random_state=42)
                    X, y = rus.fit_resample(X, y)
                st.info(f"Applied {sampling} sampling. New dataset size: {len(X)}")
            except Exception as e:
                st.warning(f"⚠️ Sampling failed: {e}")

        # Build preprocessor
        try:
            preproc, numeric_cols, cat_cols, get_feature_names = build_preprocessor(
                df, target, 
                encoding_strategy=enc_strategy,
                poly_degree=poly_degree,
                include_interactions=include_interactions
            )
        except Exception as e:
            st.error(f"❌ Preprocessing failed: {e}")
            return

        # Create and train model
        try:
            model = model_key_to_estimator(model_choice, ptype)
            pipe = Pipeline([('preproc', preproc), ('model', model)])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_frac, random_state=42,
                stratify=y if ptype == "Classification" and len(np.unique(y)) > 1 else None
            )
            
            # Train model
            with st.spinner("Training model..."):
                pipe.fit(X_train, y_train)
            
            # Make predictions
            y_pred = pipe.predict(X_test)
            
            # Store pipeline in session state
            st.session_state.pipeline = pipe
            
            # Display results
            st.success("✅ Model trained successfully!")
            log_change("Trained model", f"Model: {model_choice}, Test size: {test_frac}")
            
            # Show metrics
            st.markdown("### 📊 Model Performance")
            if ptype == "Classification":
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Accuracy", f"{accuracy_score(y_test, y_pred):.4f}")
                with col2:
                    st.metric("Precision", f"{precision_score(y_test, y_pred, average='weighted'):.4f}")
                with col3:
                    st.metric("Recall", f"{recall_score(y_test, y_pred, average='weighted'):.4f}")
                with col4:
                    st.metric("F1-Score", f"{f1_score(y_test, y_pred, average='weighted'):.4f}")
                
                # Additional metrics for binary classification
                if len(np.unique(y)) == 2:
                    try:
                        from sklearn.metrics import roc_auc_score, log_loss
                        y_pred_proba = pipe.predict_proba(X_test)[:, 1]
                        st.markdown("### 📈 Additional Classification Metrics")
                        col5, col6 = st.columns(2)
                        with col5:
                            st.metric("ROC AUC", f"{roc_auc_score(y_test, y_pred_proba):.4f}")
                        with col6:
                            st.metric("Log Loss", f"{log_loss(y_test, y_pred_proba):.4f}")
                    except:
                        pass
                
                # Classification report
                st.markdown("### 📋 Detailed Classification Report")
                st.text(classification_report(y_test, y_pred))
                
                # Confusion Matrix
                st.markdown("### 📊 Confusion Matrix")
                cm = confusion_matrix(y_test, y_pred)
                cm_df = pd.DataFrame(cm, index=np.unique(y), columns=np.unique(y))
                fig = px.imshow(cm_df, text_auto=True, aspect="auto", 
                               title="Confusion Matrix",
                               labels=dict(x="Predicted", y="Actual", color="Count"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("R² Score", f"{r2_score(y_test, y_pred):.4f}")
                with col2:
                    st.metric("RMSE", f"{np.sqrt(mean_squared_error(y_test, y_pred)):.4f}")
                with col3:
                    st.metric("MAE", f"{mean_absolute_error(y_test, y_pred):.4f}")
                
                # Additional regression metrics
                try:
                    st.markdown("### 📈 Additional Regression Metrics")
                    col4, col5 = st.columns(2)
                    with col4:
                        st.metric("MAPE", f"{np.mean(np.abs((y_test - y_pred) / y_test)) * 100:.2f}%")
                    with col5:
                        if np.all(y_test > 0) and np.all(y_pred > 0):
                            st.metric("RMSLE", f"{np.sqrt(mean_squared_log_error(y_test, y_pred)):.4f}")
                except:
                    pass
                
                # Actual vs Predicted plot
                st.markdown("### 📊 Actual vs Predicted")
                fig = px.scatter(x=y_test, y=y_pred, 
                                labels={'x': 'Actual', 'y': 'Predicted'},
                                title="Actual vs Predicted Values")
                fig.add_shape(type='line', x0=y_test.min(), y0=y_test.min(),
                             x1=y_test.max(), y1=y_test.max(),
                             line=dict(color='red', dash='dash'))
                st.plotly_chart(fig, use_container_width=True)
            
            # Feature importance (if available)
            if hasattr(model, 'feature_importances_'):
                try:
                    st.markdown("### 🎯 Feature Importance")
                    feature_names = get_feature_names(preproc)
                    if len(feature_names) == len(model.feature_importances_):
                        importance_df = pd.DataFrame({
                            'feature': feature_names,
                            'importance': model.feature_importances_
                        }).sort_values('importance', ascending=False).head(20)
                        
                        st.dataframe(importance_df, use_container_width=True)
                        
                        # Plot feature importance
                        fig = px.bar(importance_df, x='importance', y='feature', orientation='h',
                                    title='Top 20 Feature Importances')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        # Fallback when feature names don't match
                        importance_df = pd.DataFrame({
                            'feature': [f"Feature_{i}" for i in range(len(model.feature_importances_))],
                            'importance': model.feature_importances_
                        }).sort_values('importance', ascending=False).head(20)
                        st.dataframe(importance_df, use_container_width=True)
                except Exception as e:
                    logger.warning(f"Feature importance plotting failed: {e}")
            
            # SHAP explanation (if available)
            if SHAP_AVAILABLE and st.checkbox("Explain with SHAP (may take a while)"):
                try:
                    import shap
                    with st.spinner("Computing SHAP values..."):
                        # Use a sample for SHAP to speed up computation
                        sample_size = min(100, len(X_train))
                        X_sample = X_train.sample(n=sample_size, random_state=42)
                        
                        explainer = shap.Explainer(pipe.predict, X_sample)
                        shap_values = explainer(X_sample)
                        
                        st.markdown("### 🔍 SHAP Feature Explanation")
                        shap.plots.waterfall(shap_values[0])
                        st.pyplot()
                except Exception as e:
                    st.warning(f"SHAP explanation failed: {e}")
                    
        except Exception as e:
            st.error(f"❌ Model training failed: {e}")
            logger.error(f"Model training error: {e}")


def _render_model_evaluation(df: pd.DataFrame) -> None:
    st.markdown("### 📊 Model Diagnostics")
    
    if "pipeline" not in st.session_state or st.session_state.pipeline is None:
        st.info("🎯 Train a model first in the 'Quick Train' tab.")
        return
    
    # Learning curve analysis
    st.markdown("#### 📈 Learning Curve Analysis")
    if st.button("Generate Learning Curve"):
        with st.spinner("Computing learning curve..."):
            try:
                pipe = st.session_state.pipeline
                target = st.session_state.target_col
                ptype = st.session_state.problem_type
                
                # Get data
                df_data = st.session_state.work_df
                X = df_data.drop(columns=[target])
                y = df_data[target]
                if ptype == "Classification" and y.dtype == object:
                    y = pd.factorize(y)[0]
                
                # Compute learning curve
                train_sizes, train_scores, val_scores = learning_curve(
                    pipe, X, y, cv=5, n_jobs=N_JOBS, 
                    train_sizes=np.linspace(0.1, 1.0, 10),
                    scoring="accuracy" if ptype == "Classification" else "r2"
                )
                
                # Plot learning curve
                train_mean = np.mean(train_scores, axis=1)
                train_std = np.std(train_scores, axis=1)
                val_mean = np.mean(val_scores, axis=1)
                val_std = np.std(val_scores, axis=1)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=train_sizes, y=train_mean,
                    mode='lines+markers',
                    name='Training Score',
                    line=dict(color='blue'),
                    error_y=dict(type='data', array=train_std, visible=True)
                ))
                fig.add_trace(go.Scatter(
                    x=train_sizes, y=val_mean,
                    mode='lines+markers',
                    name='Validation Score',
                    line=dict(color='red'),
                    error_y=dict(type='data', array=val_std, visible=True)
                ))
                fig.update_layout(
                    title='Learning Curve',
                    xaxis_title='Training Set Size',
                    yaxis_title='Score',
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Interpretation
                final_train_score = train_mean[-1]
                final_val_score = val_mean[-1]
                
                if final_val_score < 0.7:
                    st.warning("⚠️ Low validation score suggests the model may be underfitting. Consider more complex models or feature engineering.")
                elif abs(final_train_score - final_val_score) > 0.1:
                    st.warning("⚠️ Gap between training and validation scores suggests overfitting. Consider regularization or more data.")
                else:
                    st.success("✅ Model appears to be well-fitted.")
                    
            except Exception as e:
                st.error(f"❌ Failed to compute learning curve: {e}")


def _run_optuna_trial(
    df: pd.DataFrame,
    target: str,
    ptype: str,
    model_name: str,
    n_trials: int,
    scoring: str,
    selected_features: List[str],
    timeout: int = 120  # Adding timeout parameter with default value
) -> Tuple[Dict[str, Any], float]:
    """
    Run hyperparameter tuning using Optuna.
    
    Parameters:
    - df: DataFrame containing the data.
    - target: Name of the target column.
    - ptype: Problem type ('Classification' or 'Regression').
    - model_name: Name of the model to tune.
    - n_trials: Number of trials for Optuna.
    - scoring: Scoring metric for cross-validation.
    - selected_features: List of selected features to use.
    - timeout: Timeout in seconds for the optimization.
    
    Returns:
    - best_params: Dictionary of best hyperparameters.
    - best_score: Best cross-validation score.
    """
    X = df[selected_features]
    y = df[target]
    if ptype == "Classification" and y.dtype == object:
        y = pd.factorize(y)[0]
    
    preprocessor = build_preprocessor(df, target)
    
    def objective(trial: optuna.Trial) -> float:
        if 'RandomForest' in model_name:
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 20),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'n_jobs': N_JOBS  # Use the N_JOBS constant from config
            }
            
            if ptype == "Classification":
                model = RandomForestClassifier(**params, random_state=42)
            else:
                model = RandomForestRegressor(**params, random_state=42)
                
        elif 'LogisticRegression' in model_name or model_name == 'Logistic Regression':
            params = {
                'C': trial.suggest_float('C', 0.01, 10.0, log=True),
                'penalty': trial.suggest_categorical('penalty', ['l1', 'l2', 'elasticnet']) if ptype == "Classification" else 'l2',
                'solver': 'saga'  # Needed to support various penalties
            }
            
            if ptype == "Classification":
                model = LogisticRegression(**params, random_state=42, n_jobs=N_JOBS)
            else:
                # For regression, use Ridge or Lasso instead
                if params['penalty'] == 'l1':
                    model = Lasso(alpha=params['C'], random_state=42)
                elif params['penalty'] == 'l2':
                    model = Ridge(alpha=params['C'], random_state=42)
                else:
                    model = LinearRegression()
                    
        elif 'SVM' in model_name or 'Support Vector' in model_name:
            params = {
                'C': trial.suggest_float('C', 0.01, 10.0, log=True),
                'gamma': trial.suggest_categorical('gamma', ['scale', 'auto']),
            }
            
            if ptype == "Classification":
                model = SVC(**params, random_state=42)
            else:
                model = SVR(**params)
        else:
            # Default to random forest for other cases
            if ptype == "Classification":
                model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=N_JOBS)
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=N_JOBS)
        
        pipe = Pipeline([('preprocessor', preprocessor), ('model', model)])
        
        # Cross-validation scoring
        scores = cross_val_score(pipe, X, y, cv=min(3, len(X)//5), scoring=scoring, n_jobs=1)
        return scores.mean()
    
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials, timeout=timeout)
    
    return study.best_params, study.best_value


def _render_advanced_tuning(df: pd.DataFrame) -> None:
    st.markdown("### ⚙️ Hyperparameter Tuning")
    
    if not OPTUNA_READY:
        st.warning("⚠️ Optuna not installed. Install with: `pip install optuna`")
        return
        
    if "target_col" not in st.session_state:
        st.info("🎯 Target column not set. Define it in the setup step.")
        return
        
    target = st.session_state.target_col
    ptype = st.session_state.problem_type
    selected_features = st.session_state.selected_features
    
    st.info("💡 Hyperparameter tuning can take several minutes. Please be patient.")
    
    # Model selection for tuning
    if ptype == "Classification":
        model_options = ["Random Forest", "Logistic Regression", "SVM"]
    else:
        model_options = ["Random Forest", "Ridge/Lasso", "SVR"]
    
    model_to_tune = st.selectbox("Model to tune", model_options, index=0)
    
    # Tuning options
    n_trials = st.slider("Number of trials", 10, 200, 50)
    timeout = st.slider("Timeout (seconds)", 30, 600, 120)
    
    # Scoring metric
    if ptype == "Classification":
        scoring_options = ["accuracy", "f1_weighted", "precision_weighted", "recall_weighted", "roc_auc"]
    else:
        scoring_options = ["r2", "neg_root_mean_squared_error", "neg_mean_absolute_error"]
    
    scoring = st.selectbox("Optimization metric", scoring_options, index=0)
    
    if st.button("🔍 Start Tuning", type="primary"):
        with st.spinner("Tuning hyperparameters..."):
            try:
                best_params, best_score = _run_optuna_trial(
                    df, target, ptype, model_to_tune, n_trials, scoring, selected_features
                )
                
                st.success("✅ Tuning completed!")
                
                # Display results
                results_df = pd.DataFrame({
                    'Parameter': list(best_params.keys()),
                    'Value': list(best_params.values()),
                })
                
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(results_df, use_container_width=True)
                with col2:
                    st.metric(label="Best CV Score", value=f"{best_score:.4f}")
                
                # Store best parameters in session state for potential use
                st.session_state.last_tuned_params = best_params
                st.session_state.last_tuned_score = best_score
                st.session_state.last_tuned_model = model_to_tune
                
                st.info(f"Best parameters stored for {model_to_tune}. You can now use these in model building.")
                
            except Exception as e:
                st.error(f"❌ Tuning failed: {e}")
                logger.exception("Tuning error")


def _render_unsupervised_model_building(df: pd.DataFrame) -> None:
    selected_features = st.session_state.selected_features
    task = st.session_state.unsupervised_task
    
    if task == "Clustering":
        _render_clustering_analysis(df)
    elif task == "Dimensionality Reduction":
        _render_dimensionality_reduction(df)
    elif task == "Anomaly Detection":
        _render_anomaly_detection(df, selected_features)
    else:
        st.info("Unknown task selected.")


def _render_anomaly_detection(df, selected_features):
    from sklearn.ensemble import IsolationForest
    import plotly.graph_objects as go
    
    st.markdown("### 🚨 Anomaly Detection")
    
    X = df[selected_features].select_dtypes(include=[np.number]).dropna()
    if X.empty:
        st.warning("⚠️ No numeric features available for anomaly detection. Please select numeric features.")
        return
    
    contamination = st.slider("Expected anomaly fraction", 0.01, 0.3, 0.05, help="Expected proportion of anomalies in the dataset")
    
    # Add algorithm selection
    algo = st.selectbox("Select algorithm", ["Isolation Forest", "Local Outlier Factor"], help="Choose the anomaly detection algorithm")
    
    if algo == "Isolation Forest":
        clf = IsolationForest(contamination=contamination, random_state=42, n_jobs=N_JOBS)
        scores = clf.fit_predict(X)
        anomaly_scores = clf.decision_function(X)
    else:  # Local Outlier Factor
        from sklearn.neighbors import LocalOutlierFactor
        clf = LocalOutlierFactor(contamination=contamination, n_jobs=N_JOBS)
        scores = clf.fit_predict(X)
        anomaly_scores = clf.negative_outlier_factor_
    
    # Create results dataframe
    anomaly_df = df.copy()
    anomaly_df['anomaly_score'] = anomaly_scores
    anomaly_df['is_anomaly'] = scores == -1
    
    n_anomalies = (scores == -1).sum()
    pct_anomalies = n_anomalies / len(scores) * 100
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Anomalies", f"{n_anomalies:,}")
    with col2:
        st.metric("Anomaly Rate", f"{pct_anomalies:.2f}%")
    with col3:
        st.metric("Normal Points", f"{len(scores) - n_anomalies:,}")
    
    # Show anomalies
    st.subheader("Detected Anomalies")
    anomalous_data = anomaly_df[anomaly_df['is_anomaly']].copy()
    
    if not anomalous_data.empty:
        st.dataframe(anomalous_data.head(50), use_container_width=True)
        
        # Visualize anomalies if we have at least 2 numeric features
        numeric_cols = X.columns.tolist()
        if len(numeric_cols) >= 2:
            st.subheader("Visualization of Anomalies")
            
            x_axis = st.selectbox("X-axis", numeric_cols, index=0, key="anomaly_x_axis")
            y_axis = st.selectbox("Y-axis", numeric_cols, index=min(1, len(numeric_cols)-1), key="anomaly_y_axis")
            
            # Create scatter plot with anomalies highlighted
            fig = px.scatter(
                anomaly_df, 
                x=x_axis, 
                y=y_axis,
                color='is_anomaly',
                color_discrete_map={True: 'red', False: 'blue'},
                title='Anomaly Detection Results',
                labels={'is_anomaly': 'Is Anomaly'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need at least 2 numeric features to visualize anomalies.")
    else:
        st.info("No anomalies detected with the current settings.")


def _render_clustering_analysis(df: pd.DataFrame) -> None:
    st.markdown("### 🧩 Clustering Analysis")
    
    selected_features = st.session_state.selected_features
    df_filtered = df[selected_features]
    
    # Clustering algorithm selection
    clustering_algo = st.selectbox(
        "Select clustering algorithm",
        ("K-Means", "DBSCAN"),
        help="K-Means: Partition data into K clusters. DBSCAN: Find clusters based on density."
    )
    
    # Preprocessing options
    st.markdown("#### 🔧 Preprocessing")
    
    # Scaling
    scaling_option = st.selectbox(
        "Select scaling method",
        ("None", "Standard Scaling", "Min-Max Scaling"),
        index=1
    )
    
    # Dimensionality reduction
    use_pca = st.checkbox("Apply PCA for dimensionality reduction")
    n_components = 2
    if use_pca:
        max_components = min(len(selected_features), 20)
        n_components = st.slider("Number of PCA components", 2, max_components, min(5, max_components))
    
    # Algorithm-specific parameters
    if clustering_algo == "K-Means":
        n_clusters = st.slider("Number of clusters", 2, 20, 3)
        n_init = st.slider("Number of initializations", 1, 20, 10)
    else:  # DBSCAN
        eps = st.slider("Epsilon (neighborhood radius)", 0.1, 5.0, 0.5)
        min_samples = st.slider("Minimum samples", 1, 20, 5)
    
    if st.button("🚀 Run Clustering Analysis", type="primary"):
        with st.spinner("Running clustering analysis..."):
            try:
                # Prepare data
                X = df_filtered.copy()
                
                # Apply scaling
                if scaling_option == "Standard Scaling":
                    from sklearn.preprocessing import StandardScaler
                    scaler = StandardScaler()
                    X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
                elif scaling_option == "Min-Max Scaling":
                    from sklearn.preprocessing import MinMaxScaler
                    scaler = MinMaxScaler()
                    X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
                
                # Apply PCA if requested
                if use_pca:
                    pca = PCA(n_components=n_components)
                    X_pca = pca.fit_transform(X)
                    st.info(f"PCA explained variance ratio: {pca.explained_variance_ratio_.sum():.2%}")
                else:
                    X_pca = X.values
                
                # Apply clustering algorithm
                if clustering_algo == "K-Means":
                    clusterer = KMeans(n_clusters=n_clusters, n_init=n_init, random_state=42)
                    cluster_labels = clusterer.fit_predict(X_pca)
                else:  # DBSCAN
                    clusterer = DBSCAN(eps=eps, min_samples=min_samples)
                    cluster_labels = clusterer.fit_predict(X_pca)
                
                # Store results
                st.session_state.unsupervised_model = clusterer
                st.session_state.cluster_labels = cluster_labels
                st.session_state.X_processed = X_pca
                
                # Display results
                n_clusters_found = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
                n_noise_points = list(cluster_labels).count(-1)
                
                st.success(f"✅ Clustering completed with {n_clusters_found} clusters and {n_noise_points} noise points")
                
                # Evaluation metrics (only if not all points are noise)
                if len(set(cluster_labels)) > 1 and -1 not in set(cluster_labels):
                    try:
                        silhouette_avg = silhouette_score(X_pca, cluster_labels)
                        calinski_harabasz = calinski_harabasz_score(X_pca, cluster_labels)
                        davies_bouldin = davies_bouldin_score(X_pca, cluster_labels)
                        
                        st.markdown("### 📊 Clustering Metrics")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Silhouette Score", f"{silhouette_avg:.3f}")
                        with col2:
                            st.metric("Calinski-Harabasz Index", f"{calinski_harabasz:.1f}")
                        with col3:
                            st.metric("Davies-Bouldin Index", f"{davies_bouldin:.3f}")
                        
                        # Interpretation
                        if silhouette_avg > 0.5:
                            st.success("✅ Good clustering structure (silhouette score > 0.5)")
                        elif silhouette_avg > 0.25:
                            st.info("ℹ️ Reasonable clustering structure (silhouette score > 0.25)")
                        else:
                            st.warning("⚠️ Poor clustering structure (silhouette score < 0.25)")
                    except Exception as e:
                        st.warning(f"⚠️ Could not compute clustering metrics: {e}")
                
                # Visualization
                st.markdown("### 📈 Clustering Visualization")
                
                # If we have more than 2 dimensions, use PCA or t-SNE for visualization
                if X_pca.shape[1] > 2:
                    # Use t-SNE for visualization
                    tsne = TSNE(n_components=2, random_state=42)
                    X_vis = tsne.fit_transform(X_pca)
                    x_label, y_label = "t-SNE 1", "t-SNE 2"
                else:
                    X_vis = X_pca
                    x_label, y_label = selected_features[0], selected_features[1] if len(selected_features) > 1 else selected_features[0]
                
                # Create scatter plot
                vis_df = pd.DataFrame({
                    x_label: X_vis[:, 0],
                    y_label: X_vis[:, 1],
                    'Cluster': [f"Cluster {label}" if label != -1 else "Noise" for label in cluster_labels]
                })
                
                fig = px.scatter(
                    vis_df, 
                    x=x_label, 
                    y=y_label, 
                    color='Cluster',
                    title=f"{clustering_algo} Clustering Results"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Cluster statistics
                st.markdown("### 📊 Cluster Statistics")
                cluster_stats = pd.DataFrame({
                    'Cluster': np.unique(cluster_labels),
                    'Size': [list(cluster_labels).count(label) for label in np.unique(cluster_labels)]
                }).sort_values('Size', ascending=False)
                st.dataframe(cluster_stats, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Clustering failed: {e}")
                logger.error(f"Clustering error: {e}")


def _render_dimensionality_reduction(df: pd.DataFrame) -> None:
    st.markdown("### 📉 Dimensionality Reduction")
    
    selected_features = st.session_state.selected_features
    df_filtered = df[selected_features]
    
    # Method selection
    reduction_method = st.selectbox(
        "Select dimensionality reduction method",
        ("PCA", "t-SNE"),
        help="PCA: Linear dimensionality reduction. t-SNE: Non-linear dimensionality reduction good for visualization."
    )
    
    # Preprocessing
    st.markdown("#### 🔧 Preprocessing")
    scaling_option = st.selectbox(
        "Select scaling method",
        ("None", "Standard Scaling", "Min-Max Scaling"),
        index=1
    )
    
    # Parameters
    n_components = st.slider("Number of components", 2, min(10, len(selected_features)), 2)
    
    if reduction_method == "t-SNE":
        perplexity = st.slider("Perplexity", 5, 50, 30)
        n_iter = st.slider("Number of iterations", 250, 2000, 1000)
    
    if st.button("🚀 Apply Dimensionality Reduction", type="primary"):
        with st.spinner(f"Applying {reduction_method}..."):
            try:
                # Prepare data
                X = df_filtered.copy()
                
                # Apply scaling
                if scaling_option == "Standard Scaling":
                    from sklearn.preprocessing import StandardScaler
                    scaler = StandardScaler()
                    X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
                elif scaling_option == "Min-Max Scaling":
                    from sklearn.preprocessing import MinMaxScaler
                    scaler = MinMaxScaler()
                    X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
                
                # Apply dimensionality reduction
                if reduction_method == "PCA":
                    reducer = PCA(n_components=n_components)
                    X_reduced = reducer.fit_transform(X)
                    explained_variance = reducer.explained_variance_ratio_
                    st.info(f"Total explained variance: {explained_variance.sum():.2%}")
                else:  # t-SNE
                    reducer = TSNE(n_components=n_components, perplexity=perplexity, n_iter=n_iter, random_state=42)
                    X_reduced = reducer.fit_transform(X)
                
                # Store results
                st.session_state.dimensionality_reducer = reducer
                st.session_state.X_reduced = X_reduced
                
                # Visualization
                st.markdown("### 📈 Reduced Dimensions Visualization")
                
                if n_components >= 2:
                    reduced_df = pd.DataFrame({
                        'Component 1': X_reduced[:, 0],
                        'Component 2': X_reduced[:, 1] if n_components > 1 else np.zeros(len(X_reduced))
                    })
                    
                    fig = px.scatter(reduced_df, x='Component 1', y='Component 2', 
                                   title=f"{reduction_method} Visualization")
                    st.plotly_chart(fig, use_container_width=True)
                
                if reduction_method == "PCA" and n_components >= 2:
                    # Show explained variance
                    st.markdown("### 📊 Explained Variance")
                    variance_df = pd.DataFrame({
                        'Component': [f"PC{i+1}" for i in range(len(explained_variance))],
                        'Explained Variance Ratio': explained_variance
                    })
                    st.dataframe(variance_df.style.format({"Explained Variance Ratio": "{:.2%}"}), use_container_width=True)
                    
                    # Scree plot
                    fig = px.bar(variance_df, x='Component', y='Explained Variance Ratio',
                               title="Scree Plot")
                    st.plotly_chart(fig, use_container_width=True)
                
                st.success(f"✅ {reduction_method} completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Dimensionality reduction failed: {e}")
                logger.error(f"Dimensionality reduction error: {e}")


# =============== STEP 6: MODEL DEPLOYMENT ===============
def _render_model_deployment(df: pd.DataFrame) -> None:
    if st.session_state.learning_type == "Supervised":
        _render_supervised_deployment(df)
    else:
        _render_unsupervised_deployment(df)


def _render_supervised_deployment(df: pd.DataFrame) -> None:
    st.markdown("### 🚀 Model Deployment")
    
    if "pipeline" not in st.session_state or st.session_state.pipeline is None:
        st.info("🎯 Train a model first in the 'Quick Train' section.")
        return
    
    tabs = st.tabs(["🐍 Export Code", "📦 Export Model"])
    
    with tabs[0]:
        _render_export_code()
    
    with tabs[1]:
        _render_export_model()


def _render_unsupervised_deployment(df: pd.DataFrame) -> None:
    st.markdown("### 🚀 Model Deployment")
    
    if "unsupervised_model" not in st.session_state:
        st.info("🎯 Run an unsupervised analysis first.")
        return
    
    tabs = st.tabs(["🐍 Export Code", "📦 Export Model"])
    
    with tabs[0]:
        _render_unsupervised_export_code()
    
    with tabs[1]:
        _render_unsupervised_export_model()


def _render_model_cards() -> None:
    st.markdown("### 📋 Model Information")
    
    if "pipeline" not in st.session_state or st.session_state.pipeline is None:
        st.info("🎯 Train a model first.")
        return
        
    pipe = st.session_state.pipeline
    
    # Model steps
    st.markdown("#### 🔧 Pipeline Steps")
    for i, (name, step) in enumerate(pipe.steps):
        st.write(f"{i+1}. **{name}**: {type(step).__name__}")
        
    # Preprocessing details
    preproc = pipe.named_steps.get('preproc')
    if preproc:
        st.markdown("#### 🔄 Preprocessing Details")
        if hasattr(preproc, 'transformers_'):
            for name, transformer, features in preproc.transformers_:
                if hasattr(transformer, 'named_steps'):
                    steps = [s[0] for s in transformer.steps]
                    st.write(f"- **{name}** ({', '.join(features) if isinstance(features, list) else features}): {', '.join(steps)}")
                else:
                    st.write(f"- **{name}**: {type(transformer).__name__}")
    
    # Model parameters
    model = pipe.named_steps.get('model')
    if model:
        st.markdown("#### ⚙️ Model Parameters")
        params = model.get_params()
        param_df = pd.DataFrame(list(params.items()), columns=['Parameter', 'Value'])
        st.dataframe(param_df, use_container_width=True, hide_index=True)


def _render_export_code() -> None:
    st.markdown("### 🐍 Export Python Code")
    
    if "pipeline" not in st.session_state or st.session_state.pipeline is None:
        st.info("🎯 Train a model first.")
        return
        
    if "target_col" not in st.session_state:
        st.info("🎯 Target column not set.")
        return
        
    target = st.session_state.target_col
    ptype = st.session_state.problem_type
    selected_features = st.session_state.selected_features if 'selected_features' in st.session_state else []
    
    pipe = st.session_state.pipeline
    
    # Generate comprehensive code snippet that includes the entire workflow
    code_snippet = f'''# Auto-generated Machine Learning Pipeline
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Problem Type: {ptype}
# Target Column: {target}

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                           r2_score, mean_squared_error, mean_absolute_error)

# Model-specific imports based on your selection
# You may need to install additional packages:
# pip install scikit-learn

'''
    
    # Add model-specific imports
    model = pipe.named_steps.get('model')
    model_type = type(model).__name__
    
    if 'XGB' in model_type:
        code_snippet += 'import xgboost as xgb\n'
    elif 'LGBM' in model_type:
        code_snippet += 'import lightgbm as lgb\n'
    elif 'CatBoost' in model_type:
        code_snippet += 'from catboost import CatBoostClassifier, CatBoostRegressor\n'
    
    code_snippet += '''
# Load your dataset
# Replace 'your_dataset.csv' with the actual path to your dataset
df = pd.read_csv("your_dataset.csv")

# Selected features and target
'''
    
    if selected_features:
        code_snippet += f'''selected_features = {selected_features}
target = '{target}'

X = df[selected_features]
y = df[target]
'''
    else:
        code_snippet += f'''target = '{target}'
X = df.drop(columns=[target])
y = df[target]
'''

    # Add feature engineering steps
    code_snippet += '''
# Feature Engineering Steps
# Apply the same preprocessing steps used in the Streamlit app
'''

    # Handle missing values
    if 'missing_value_strategy' in st.session_state:
        strategy = st.session_state.missing_value_strategy
        if strategy == "Drop rows with missing values":
            code_snippet += '''# Drop rows with missing values
X = X.dropna()
y = y.loc[X.index]
'''
        elif strategy in ["Mean imputation", "Median imputation", "Mode imputation"]:
            impute_method = "mean" if strategy == "Mean imputation" else \
                           "median" if strategy == "Median imputation" else "most_frequent"
            code_snippet += f'''# Impute missing values with {strategy.lower()}
imputer = SimpleImputer(strategy='{impute_method}')
X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
'''

    # Handle encoding
    if 'encoding_method' in st.session_state and st.session_state.encoding_method != "None":
        encoding = st.session_state.encoding_method
        code_snippet += f'''
# Categorical encoding: {encoding}
# Note: In a production environment, you should save and reuse the fitted encoders
'''
        if encoding == "One-Hot Encoding":
            code_snippet += '''# One-hot encode categorical features
X = pd.get_dummies(X, drop_first=True)
'''
        elif encoding == "Label Encoding":
            code_snippet += '''# Label encode categorical features
# Note: This applies label encoding to all object-type columns
categorical_columns = X.select_dtypes(include=['object']).columns
for col in categorical_columns:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))
'''

    # Handle scaling
    if 'scaling_method' in st.session_state and st.session_state.scaling_method != "None":
        scaling = st.session_state.scaling_method
        code_snippet += f'''
# Feature scaling: {scaling}
'''
        
        if scaling == "Standard Scaling (Z-score)":
            code_snippet += '''scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X = pd.DataFrame(X_scaled, columns=X.columns)
'''
        elif scaling == "Min-Max Scaling":
            code_snippet += '''scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)
X = pd.DataFrame(X_scaled, columns=X.columns)
'''
        elif scaling == "Robust Scaling":
            code_snippet += '''scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)
X = pd.DataFrame(X_scaled, columns=X.columns)
'''
        elif scaling == "MaxAbs Scaling":
            code_snippet += '''scaler = MaxAbsScaler()
X_scaled = scaler.fit_transform(X)
X = pd.DataFrame(X_scaled, columns=X.columns)
'''

    # Add train/test split
    code_snippet += '''
# Train-test split
# Using the same test size as in the Streamlit app (default 0.2)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
'''

    # Add model training code
    code_snippet += f'''
# Model Training
# Model type: {model_type}
'''

    # Generate model initialization code based on the actual model
    if 'XGB' in model_type:
        if ptype == "Classification":
            code_snippet += f'''model = xgb.XGBClassifier(**{str(model.get_params())})
'''
        else:
            code_snippet += f'''model = xgb.XGBRegressor(**{str(model.get_params())})
'''
    elif 'LGBM' in model_type:
        if ptype == "Classification":
            code_snippet += f'''model = lgb.LGBMClassifier(**{str(model.get_params())})
'''
        else:
            code_snippet += f'''model = lgb.LGBMRegressor(**{str(model.get_params())})
'''
    elif 'CatBoost' in model_type:
        if ptype == "Classification":
            code_snippet += f'''model = CatBoostClassifier(**{str(model.get_params())}, verbose=False)
'''
        else:
            code_snippet += f'''model = CatBoostRegressor(**{str(model.get_params())}, verbose=False)
'''
    else:
        # For scikit-learn models
        code_snippet += f'''from {model.__class__.__module__} import {model_type}
model = {model_type}(**{str(model.get_params())})
'''

    code_snippet += '''
# Fit the model
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Evaluate the model
if ptype == "Classification":
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    print(f"Accuracy: {accuracy:.2f}")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1 Score: {f1:.2f}")
else:
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"R^2 Score: {r2:.2f}")
    print(f"Mean Squared Error: {mse:.2f}")
    print(f"Mean Absolute Error: {mae:.2f}")

# Save the trained model
joblib.dump(model, "model.pkl")
print("Model saved as 'model.pkl'")
'''

    # Display the code
    st.code(code_snippet, language="python")
    
    # Download button
    st.download_button(
        label="💾 Download Code (.py)",
        data=code_snippet,
        file_name=f"{BRAND_NAME.lower()}_unsupervised_{datetime.now().strftime('%Y%m%d_%H%M')}.py",
        mime="text/plain"
    )


def _render_unsupervised_export_code() -> None:
    st.markdown("### 🐍 Export Python Code")
    
    if "unsupervised_model" not in st.session_state:
        st.info("🎯 Run an unsupervised analysis first.")
        return
    
    task = st.session_state.unsupervised_task
    selected_features = st.session_state.selected_features if 'selected_features' in st.session_state else []
    
    # Generate comprehensive code snippet for unsupervised learning
    code_snippet = f'''# Auto-generated Unsupervised Learning Pipeline
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Task Type: {task}
# Selected Features: {selected_features}

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

# Load your dataset
# Replace 'your_dataset.csv' with the actual path to your dataset
df = pd.read_csv("your_dataset.csv")

# Selected features
selected_features = {selected_features}
X = df[selected_features]

# Preprocessing
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Apply {task} algorithm
# This is a template - customize parameters as needed
'''
    
    if task == "Clustering":
        if hasattr(st.session_state.unsupervised_model, 'n_clusters'):
            n_clusters = st.session_state.unsupervised_model.n_clusters
            code_snippet += f"""# K-Means Clustering
kmeans = KMeans(n_clusters={n_clusters}, random_state=42)
cluster_labels = kmeans.fit_predict(X_scaled)

# Evaluate clustering
silhouette_avg = silhouette_score(X_scaled, cluster_labels)
print(f'Silhouette Score: {{silhouette_avg:.3f}}')
"""
        elif st.session_state.unsupervised_task == "Clustering":
            # Default to 3 clusters if not specifically set
            code_snippet += """# K-Means Clustering
kmeans = KMeans(n_clusters=3, random_state=42)
cluster_labels = kmeans.fit_predict(X_scaled)

# Evaluate clustering
silhouette_avg = silhouette_score(X_scaled, cluster_labels)
print(f'Silhouette Score: {silhouette_avg:.3f}')
"""

    elif task == "Dimensionality Reduction":
        if 'dimensionality_reducer' in st.session_state:
            reducer = st.session_state.dimensionality_reducer
            if hasattr(reducer, 'n_components'):
                n_components = reducer.n_components
                code_snippet += f"""# Principal Component Analysis
pca = PCA(n_components={n_components})
X_reduced = pca.fit_transform(X_scaled)

# Explained variance
print(f'Explained variance ratio: {{pca.explained_variance_ratio_}}')
print(f'Total explained variance: {{pca.explained_variance_ratio_.sum():.2%}}')
"""
            else:
                code_snippet += """# Principal Component Analysis
pca = PCA(n_components=2)  # Default to 2 components
X_reduced = pca.fit_transform(X_scaled)

# Explained variance
print(f'Explained variance ratio: {pca.explained_variance_ratio_}')
print(f'Total explained variance: {pca.explained_variance_ratio_.sum():.2%}')
"""
        else:
            code_snippet += """# Principal Component Analysis
pca = PCA(n_components=2)  # Default to 2 components
X_reduced = pca.fit_transform(X_scaled)

# Explained variance
print(f'Explained variance ratio: {pca.explained_variance_ratio_}')
print(f'Total explained variance: {pca.explained_variance_ratio_.sum():.2%}')
"""

    elif task == "Anomaly Detection":
        code_snippet += """# Anomaly Detection with Isolation Forest
from sklearn.ensemble import IsolationForest

isolation_forest = IsolationForest(contamination=0.1, random_state=42)
anomaly_labels = isolation_forest.fit_predict(X_scaled)

# Anomalies are labeled as -1, normal points as 1
n_anomalies = list(anomaly_labels).count(-1)
print(f'Number of anomalies detected: {n_anomalies}')
"""

    else:
        code_snippet += """# Placeholder for other unsupervised tasks
print("Add your custom unsupervised learning code here")
"""
    
    code_snippet += """

# Save results back to dataframe if needed
df['cluster_labels'] = cluster_labels if 'cluster_labels' in locals() else None
df['anomaly_labels'] = anomaly_labels if 'anomaly_labels' in locals() else None
df['X_reduced'] = X_reduced if 'X_reduced' in locals() else None

# Save processed dataset
df.to_csv("processed_dataset.csv", index=False)
print("Results saved to processed_dataset.csv")
"""

    # Display the code
    st.code(code_snippet, language="python")
    
    # Download button
    st.download_button(
        label="💾 Download Code (.py)",
        data=code_snippet,
        file_name=f"{BRAND_NAME.lower()}_unsupervised_{datetime.now().strftime('%Y%m%d_%H%M')}.py",
        mime="text/plain"
    )


def _render_unsupervised_export_model() -> None:
    st.markdown("### 📦 Export Trained Model")
    
    if "unsupervised_model" not in st.session_state:
        st.info("🎯 Run an unsupervised analysis first.")
        return
    
    BRAND_NAME = "FineSE"  # Default brand name
    
    if st.button("💾 Save Model (Joblib)"):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            model_filename = f"{BRAND_NAME.lower()}_unsupervised_model_{timestamp}.joblib"
            joblib.dump(st.session_state.unsupervised_model, model_filename)
            with open(model_filename, "rb") as f:
                st.download_button(
                    label="⬇️ Download Model",
                    data=f,
                    file_name=model_filename,
                    mime="application/octet-stream"
                )
            st.success(f"✅ Model saved as {model_filename}")
            log_change("Exported unsupervised model", f"Filename: {model_filename}")
        except Exception as e:
            st.error(f"❌ Failed to save model: {e}")


def _render_supervised_deployment(df: pd.DataFrame) -> None:
    st.markdown("### 🚀 Model Deployment")
    
    if "pipeline" not in st.session_state or st.session_state.pipeline is None:
        st.info("🎯 Train a model first in the 'Quick Train' section.")
        return
    
    tabs = st.tabs(["🐍 Export Code", "📦 Export Model"])
    
    with tabs[0]:
        _render_export_code()
    
    with tabs[1]:
        _render_export_model()


def _render_export_model() -> None:
    st.markdown("### 📦 Export Trained Model")
    
    if "pipeline" not in st.session_state or st.session_state.pipeline is None:
        st.info("🎯 Train a model first.")
        return
    
    if st.button("💾 Save Model (Joblib)"):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            model_filename = f"{BRAND_NAME.lower()}_model_{timestamp}.joblib"
            joblib.dump(st.session_state.pipeline, model_filename)
            with open(model_filename, "rb") as f:
                st.download_button(
                    label="⬇️ Download Model",
                    data=f,
                    file_name=model_filename,
                    mime="application/octet-stream"
                )
            st.success(f"✅ Model saved as {model_filename}")
            log_change("Exported model", f"Filename: {model_filename}")
        except Exception as e:
            st.error(f"❌ Failed to save model: {e}")


# =============== UTILITY FUNCTIONS ===============
def detect_high_cardinality(df: pd.DataFrame, threshold: int = 50) -> List[Tuple[str, int]]:
    """
    Detect columns with high cardinality (many unique values)
    """
    out = []
    for c in df.select_dtypes(include=['object','category']).columns:
        if df[c].nunique(dropna=True) > threshold:
            out.append((c, df[c].nunique()))
    return out


def date_feature_engineer(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Expand datetime column into components (year, month, day, etc.)
    """
    s = pd.to_datetime(df[col], errors='coerce')
    df[f"{col}__year"] = s.dt.year
    df[f"{col}__month"] = s.dt.month
    df[f"{col}__day"] = s.dt.day
    df[f"{col}__weekday"] = s.dt.weekday
    df[f"{col}__is_weekend"] = s.dt.weekday.isin([5,6]).astype(int)
    df[f"{col}__dayofyear"] = s.dt.dayofyear
    return df
