"""
🧹 Cleaning - Smart data cleaning and preprocessing
"""
import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px

st.set_page_config(page_title="CLEANING | FINESE2", page_icon="🧹", layout="wide")

from utils.session_state import SessionManager
from utils.styling import render_section_header
from utils.animations import animate_data_transition, show_processing_animation
from modules.cleaner import DataCleaner
from modules.ai_assistant import render_ai_settings_sidebar

SessionManager.init()


st.title("🧹 Data Cleaning Pipeline")



# Check for loaded data
if not SessionManager.has_data():
    st.warning("⚠️ No data loaded. Please load data in the Data section first.")
    st.stop()

# Get current dataframe
df = SessionManager.get_df()

# Create metrics for data quality overview
missing_values = df.isnull().sum().sum()
duplicate_rows = df.duplicated().sum()
numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
categorical_cols = len(df.select_dtypes(include=['object', 'category']).columns)

# Display key metrics in cards
st.markdown("### 📊 Data Quality Overview")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Missing Values", f"{missing_values:,}")
with col2:
    st.metric("Duplicate Rows", f"{duplicate_rows:,}")
with col3:
    st.metric("Numeric Features", numeric_cols)
with col4:
    st.metric("Categorical Features", categorical_cols)

# Undo/Redo buttons
st.markdown("### 🛠️ Workspace")
col1, col2, col3 = st.columns([1, 1, 5])
with col1:
    if st.button(f"↩️ Undo ({SessionManager.get_history_length()})", 
                 disabled=SessionManager.get_history_length() == 0):
        if SessionManager.undo():
            st.rerun()
with col2:
    if st.button(f"↪️ Redo ({SessionManager.get_future_length()})", 
                 disabled=SessionManager.get_future_length() == 0):
        if SessionManager.redo():
            st.rerun()

st.markdown("---")

# Recommendations
render_section_header("Smart Recommendations", "AI-powered cleaning suggestions")

recommendations = DataCleaner.get_recommendations(df)

if any(recommendations.values()):
    with st.expander("View Recommendations", expanded=True):
        for category, items in recommendations.items():
            if items:
                st.markdown(f"**{category.replace('_', ' ').title()}**")
                for item in items:
                    priority_color = "🔴" if item.get('priority') == 'high' else "🟡" if item.get('priority') == 'medium' else "🟢"
                    st.markdown(f"{priority_color} {item.get('column', '')}: {item['issue']} → *{item['action']}*")
else:
    st.success("✅ No major data quality issues detected!")

# Data Quality Heatmap
with st.expander("🔍 Advanced Data Quality Visualization", expanded=False):
    render_section_header("Data Quality Heatmap", "Visualize completeness, validity, and consistency")

    # Create a quality score matrix
    quality_df = pd.DataFrame(index=df.columns, columns=['Completeness', 'Uniqueness', 'Validity'])
    
    for col in df.columns:
        total_count = len(df)
        non_null_count = df[col].notna().sum()
        completeness = non_null_count / total_count
        
        unique_count = df[col].nunique()
        uniqueness = unique_count / non_null_count if non_null_count > 0 else 0
        
        # Validity is harder to assess without schema - for now, using non-null ratio as proxy
        validity = non_null_count / total_count
        
        quality_df.loc[col] = [completeness, uniqueness, validity]
    
    # Melt the dataframe for heatmap
    quality_melted = quality_df.reset_index().melt(id_vars='index', var_name='Quality Metric', value_name='Score')
    
    # Create heatmap
    fig = px.imshow(
        quality_df.T, 
        labels=dict(x="Columns", y="Quality Metrics", color="Score"),
        x=quality_df.index,
        y=quality_df.columns,
        color_continuous_scale='RdYlGn',
        aspect="auto",
        title="Data Quality Assessment"
    )
    
    fig.update_xaxes(side="bottom")
    fig.update_layout(
        width=800,
        height=300,
        xaxis_tickangle=-45,
        title_font_size=14,
        coloraxis_colorbar=dict(
            title="Quality Score",
            tickvals=[0, 0.5, 1.0],
            ticktext=["Low", "Medium", "High"]
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed quality metrics
    st.subheader("Detailed Quality Metrics")
    st.dataframe(quality_df.style.format("{:.2%}").background_gradient(cmap='RdYlGn', axis=None), 
                 use_container_width=True)

# Cleaning Operations
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Missing Values", "Outliers", "Duplicates", "Transform", "Auto Clean"])

with tab1:
    render_section_header("Handle Missing Values", "")

    missing_cols = df.columns[df.isnull().any()].tolist()
    if not missing_cols:
        st.success("✅ No missing values in the dataset!")
    else:
        st.info(f"Found {len(missing_cols)} columns with missing values")

        col1, col2 = st.columns([1, 2])
        with col1:
            selected_cols = st.multiselect("Select columns", missing_cols, default=missing_cols)
            strategy = st.selectbox("Strategy", DataCleaner.CLEANING_METHODS["missing"])
            fill_value = None
            if strategy == "constant":
                fill_value = st.text_input("Fill value", "MISSING")

        with col2:
            # Preview missing stats
            missing_stats = pd.DataFrame({
                'Column': missing_cols,
                'Missing Count': [df[c].isnull().sum() for c in missing_cols],
                'Missing %': [f"{df[c].isnull().mean()*100:.1f}%" for c in missing_cols]
            })
            st.dataframe(missing_stats, use_container_width=True, hide_index=True)

        if st.button("🧹 Apply Missing Value Treatment", type="primary"):
            # Store before state for animation
            before_df = df.copy()
            
            with st.spinner("Processing..."):
                new_df, log = DataCleaner.handle_missing(df, strategy=strategy, columns=selected_cols, fill_value=fill_value)
                SessionManager.set_df(new_df, SessionManager.get("data_source"))
                SessionManager.append("cleaning_log", {"step": "missing_values", **log})
                
                # Show transition animation
                animate_data_transition(before_df, new_df, "Missing Value Treatment")
                
                st.success(f"✅ Applied {strategy} to {len(log['columns_affected'])} columns")
                if log['rows_dropped'] > 0:
                    st.info(f"Dropped {log['rows_dropped']} rows")
                st.rerun()

with tab2:
    render_section_header("Handle Outliers", "")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        st.info("No numeric columns available")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_cols = st.multiselect("Select numeric columns", numeric_cols, default=numeric_cols[:3])
            method = st.selectbox("Method", DataCleaner.CLEANING_METHODS["outliers"])

        with col2:
            # Show outlier preview
            outlier_preview = []
            for col in selected_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                count = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
                outlier_preview.append({'Column': col, 'Outliers (IQR)': count, 'Percentage': f"{count/len(df)*100:.1f}%"})
            st.dataframe(pd.DataFrame(outlier_preview), use_container_width=True, hide_index=True)

        if st.button("🧹 Apply Outlier Treatment", type="primary"):
            # Store before state for animation
            before_df = df.copy()
            
            with st.spinner("Processing..."):
                new_df, log = DataCleaner.handle_outliers(df, method=method, columns=selected_cols)
                SessionManager.set_df(new_df, SessionManager.get("data_source"))
                SessionManager.append("cleaning_log", {"step": "outliers", **log})
                
                # Show transition animation
                animate_data_transition(before_df, new_df, "Outlier Treatment")
                
                st.success(f"✅ Applied {method} to {len(log['columns_affected'])} columns")
                st.rerun()

with tab3:
    render_section_header("Handle Duplicates", "")

    dup_count = df.duplicated().sum()
    st.metric("Duplicate Rows", dup_count)

    if dup_count > 0:
        strategy = st.selectbox("Strategy", DataCleaner.CLEANING_METHODS["duplicates"])

        if st.button("🧹 Remove Duplicates", type="primary"):
            # Store before state for animation
            before_df = df.copy()
            
            with st.spinner("Processing..."):
                new_df, log = DataCleaner.handle_duplicates(df, strategy=strategy)
                SessionManager.set_df(new_df, SessionManager.get("data_source"))
                SessionManager.append("cleaning_log", {"step": "duplicates", **log})
                
                # Show transition animation
                animate_data_transition(before_df, new_df, "Duplicate Removal")
                
                st.success(f"✅ Removed {log['rows_removed']} duplicate rows")
                st.rerun()
    else:
        st.success("✅ No duplicate rows found!")

with tab4:
    render_section_header("Transform Features", "Scaling and encoding")

    subtab1, subtab2 = st.tabs(["Scaling", "Encoding"])

    with subtab1:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        selected = st.multiselect("Select columns to scale", numeric_cols, default=numeric_cols)
        method = st.selectbox("Scaling method", DataCleaner.CLEANING_METHODS["scaling"])

        if st.button("📏 Apply Scaling", type="primary"):
            with st.spinner("Scaling..."):
                new_df, log, scaler = DataCleaner.scale_features(df, method=method, columns=selected)
                SessionManager.set_df(new_df, SessionManager.get("data_source"))
                SessionManager.append("cleaning_log", {"step": "scaling", **log})
                st.success(f"✅ Applied {method} scaling")
                st.rerun()

    with subtab2:
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        selected = st.multiselect("Select columns to encode", cat_cols, default=cat_cols)
        method = st.selectbox("Encoding method", DataCleaner.CLEANING_METHODS["encoding"])
        drop_first = st.checkbox("Drop first (avoid dummy trap)", value=True) if method == "onehot" else False

        if st.button("🔤 Apply Encoding", type="primary"):
            with st.spinner("Encoding..."):
                new_df, log, encoders = DataCleaner.encode_categorical(df, method=method, columns=selected, drop_first=drop_first)
                SessionManager.set_df(new_df, SessionManager.get("data_source"))
                SessionManager.append("cleaning_log", {"step": "encoding", **log})
                st.success(f"✅ Applied {method} encoding")
                st.rerun()

with tab5:
    render_section_header("Auto Clean", "One-click smart cleaning")

    aggressive = st.checkbox("Aggressive mode (includes outlier clipping)", value=False)

    if st.button("✨ Auto Clean Everything", type="primary", use_container_width=True):
        # Store before state for animation
        before_df = df.copy()
        
        with st.spinner("Running auto-clean pipeline..."):
            new_df, logs = DataCleaner.auto_clean(df, aggressive=aggressive)
            SessionManager.set_df(new_df, SessionManager.get("data_source"))
            for log in logs:
                SessionManager.append("cleaning_log", log)

            # Show transition animation
            animate_data_transition(before_df, new_df, "Auto Clean")
            
            st.success("✅ Auto-clean complete!")
            st.markdown("**Applied steps:**")
            for log in logs:
                st.markdown(f"- {log['step']}: {log}")
            st.rerun()

# Enhanced Cleaning Log
if SessionManager.get("cleaning_log"):
    st.markdown("---")
    st.markdown("### 📝 Cleaning History")
    
    # Display logs in reverse chronological order
    for i, log in enumerate(reversed(SessionManager.get("cleaning_log"))):
        with st.expander(f"Step {len(SessionManager.get('cleaning_log')) - i}: {log['step'].replace('_', ' ').title()}", expanded=False):
            # Display log details in a more readable format
            details = {k: v for k, v in log.items() if k != 'step'}
            st.json(details)