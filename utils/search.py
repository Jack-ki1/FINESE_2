"""
Enhanced Search Functionality for FINESE2
Provides global search across data, visualizations, and analysis results
"""
import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import difflib
import re


class GlobalSearch:
    """Provides global search functionality across the application."""
    
    @staticmethod
    def search_columns(df: pd.DataFrame, query: str) -> List[Dict[str, Any]]:
        """Search for columns matching the query."""
        if df is None:
            return []
        
        results = []
        query_lower = query.lower()
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Exact match
            if query_lower == col_lower:
                results.append({
                    'type': 'column_exact',
                    'name': col,
                    'score': 100,
                    'path': f'/data#column-{col}'
                })
            # Partial match
            elif query_lower in col_lower:
                similarity = difflib.SequenceMatcher(None, query_lower, col_lower).ratio() * 100
                results.append({
                    'type': 'column_partial',
                    'name': col,
                    'score': similarity,
                    'path': f'/data#column-{col}'
                })
            # Fuzzy match
            else:
                similarity = difflib.SequenceMatcher(None, query_lower, col_lower).ratio() * 100
                if similarity > 40:  # Only include if somewhat similar
                    results.append({
                        'type': 'column_fuzzy',
                        'name': col,
                        'score': similarity,
                        'path': f'/data#column-{col}'
                    })
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:10]  # Return top 10 results
    
    @staticmethod
    def search_data_values(df: pd.DataFrame, query: str) -> List[Dict[str, Any]]:
        """Search for values in the data matching the query."""
        if df is None:
            return []
        
        results = []
        query_lower = query.lower()
        
        for col in df.columns:
            # Convert to string for searching
            str_series = df[col].astype(str)
            
            # Find rows where the query appears
            mask = str_series.str.lower().str.contains(query_lower, na=False)
            matching_indices = df[mask].index.tolist()
            
            if matching_indices:
                for idx in matching_indices[:5]:  # Limit to 5 matches per column
                    value = df.loc[idx, col]
                    results.append({
                        'type': 'data_value',
                        'column': col,
                        'row_index': idx,
                        'value': str(value)[:50],  # Truncate long values
                        'path': f'/data#cell-{idx}-{col}'
                    })
        
        return results[:20]  # Return top 20 results
    
    @staticmethod
    def search_analysis_results(query: str) -> List[Dict[str, Any]]:
        """Search in analysis results and model outputs."""
        results = []
        
        # Search in model results if available
        if 'models_trained' in st.session_state and st.session_state.models_trained:
            models_results = st.session_state.models_trained
            for model_name, model_data in models_results.get('models', {}).items():
                # Search in metrics
                for metric_name, metric_value in model_data.get('metrics', {}).items():
                    if query.lower() in metric_name.lower() or query.lower() in str(metric_value).lower():
                        results.append({
                            'type': 'model_metric',
                            'model': model_name,
                            'metric': metric_name,
                            'value': metric_value,
                            'path': '/modeling'
                        })
        
        # Search in data summaries if available
        if 'eda_html' in st.session_state and st.session_state.eda_html:
            if query.lower() in st.session_state.eda_html.lower():
                results.append({
                    'type': 'eda_report',
                    'name': 'EDA Report',
                    'path': '/eda'
                })
        
        return results
    
    @staticmethod
    def search_across_app(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Perform a comprehensive search across all app components."""
        df = None
        if 'data_frame' in st.session_state and st.session_state.data_frame is not None:
            df = st.session_state.data_frame
        
        results = {
            'columns': GlobalSearch.search_columns(df, query),
            'data_values': GlobalSearch.search_data_values(df, query),
            'analysis_results': GlobalSearch.search_analysis_results(query)
        }
        
        return results


def render_search_bar():
    """Render a global search bar component."""
    # Place search in sidebar
    with st.sidebar:
        with st.form("global_search_form"):
            st.subheader("🔍 Global Search")
            search_query = st.text_input("Search across data, columns, and results", 
                                        placeholder="Enter search term...")
            search_button = st.form_submit_button("Search", use_container_width=True, type="secondary")
        
        if search_button and search_query:
            with st.spinner("Searching..."):
                results = GlobalSearch.search_across_app(search_query)
                
                # Display results in the sidebar
                st.subheader("Search Results")
                
                total_results = sum(len(v) for v in results.values())
                if total_results == 0:
                    st.info("No results found")
                else:
                    # Expandable sections for each result type
                    if results['columns']:
                        with st.expander(f"ColumnsMode ({len(results['columns'])})", expanded=True):
                            for r in results['columns']:
                                st.markdown(f"- **{r['name']}** ({r['type']})")
                    
                    if results['data_values']:
                        with st.expander(f"Data Values ({len(results['data_values'])})", expanded=True):
                            for r in results['data_values'][:5]:  # Show first 5
                                st.markdown(f"- Row {r['row_index']}, Col '{r['column']}': {r['value']}")
                    
                    if results['analysis_results']:
                        with st.expander(f"Analysis ({len(results['analysis_results'])})", expanded=True):
                            for r in results['analysis_results']:
                                st.markdown(f"- {r['type']}: {r.get('model', r.get('name', ''))}")


def perform_global_search(query: str):
    """Perform a global search and display results."""
    if not query:
        st.warning("Please enter a search query")
        return
    
    results = GlobalSearch.search_across_app(query)
    
    st.header(f"Search Results for: '{query}'")
    
    total_results = sum(len(v) for v in results.values())
    if total_results == 0:
        st.info("No results found")
        return
    
    # Display results by category
    if results['columns']:
        with st.container():
            st.subheader(f"ColumnsMode ({len(results['columns'])})")
            col_results_df = pd.DataFrame([
                {'Column Name': r['name'], 'Match Type': r['type'], 'Relevance': f"{r['score']:.1f}%"}
                for r in results['columns']
            ])
            st.dataframe(col_results_df, use_container_width=True)
    
    if results['data_values']:
        with st.container():
            st.subheader(f"Data Matches ({len(results['data_values'])})")
            data_results_df = pd.DataFrame([
                {'Column': r['column'], 'Row Index': r['row_index'], 'Value': r['value']}
                for r in results['data_values']
            ])
            st.dataframe(data_results_df, use_container_width=True)
    
    if results['analysis_results']:
        with st.container():
            st.subheader(f"Analysis Results ({len(results['analysis_results'])})")
            analysis_results_df = pd.DataFrame([
                {'Type': r['type'], 'Detail': r.get('model', r.get('name', ''))}
                for r in results['analysis_results']
            ])
            st.dataframe(analysis_results_df, use_container_width=True)