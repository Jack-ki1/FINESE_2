import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import List, Dict, Optional, Tuple, Union
import re
import logging
from io import StringIO
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import shared utilities and config
from utils import get_numeric_columns, get_categorical_columns, log_change
from config import BRAND_NAME, SECTION_HEADER_CLASS, SECTION_SUBHEADER_CLASS, DEFAULT_LLM_MODEL, MAX_ROWS_FOR_PLOT

# Define supported LLM providers and their models
SUPPORTED_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    },
    "google": {
        "name": "Google Gemini",
        "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]
    }
}

def render_chatbot_tab(filtered: pd.DataFrame) -> None:
    """
    Unified Natural Language Data Assistant — Hybrid Rule-Based + LLM Chatbot.
    Answers questions about data: metrics, group-bys, plots, anomalies.
    Falls back to LLM only if user opts in and provides API key.
    """
    if filtered is None or filtered.empty:
        st.warning("⚠️ No data loaded. Please upload or filter data first.")
        return

    st.markdown(f'<div class="{SECTION_HEADER_CLASS}">💬 Ask Your Data</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="{SECTION_SUBHEADER_CLASS}">Ask anything: “What’s the average sales by region?” or “Show me a heatmap of correlations.”</div>', unsafe_allow_html=True)

    # --- Input Area ---
    prompt = st.text_input(
        "Type your question...",
        placeholder="e.g., 'Show top 5 products by total revenue', 'What columns have missing values?', 'Is there a correlation between price and quantity?'",
        key="chatbot_input"
    )

    # --- Toggle: Use LLM? ---
    col1, col2 = st.columns([3, 1])
    with col1:
        use_llm = st.toggle("💡 Use External AI", value=False, help="Requires API key. Slower, but understands complex questions.")
    with col2:
        if st.button("🗑️ Clear History", key="clear_history"):
            st.session_state.chat_history = []
            log_change("Cleared chat history")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # --- Process Prompt ---
    if prompt.strip():
        with st.spinner("Analyzing your data..."):
            response = _generate_response(prompt, filtered, use_llm)
            st.session_state.chat_history.append({"question": prompt, "response": response})
            log_change("Asked chatbot", f"Question: {prompt}")

        # Display latest response
        _display_response(response)

    # --- Show Conversation History ---
    if st.session_state.chat_history:
        with st.expander("📜 View Full Conversation", expanded=False):
            for i, msg in enumerate(st.session_state.chat_history):
                st.markdown(f"**Q{i+1}:** {msg['question']}")
                _display_response(msg["response"], is_history=True)
                st.markdown("---")

        # Export button
        if st.button("📥 Export Chat as Markdown"):
            markdown = _export_chat_as_markdown(st.session_state.chat_history)
            st.download_button(
                label="⬇️ Download Chat (.md)",
                data=markdown,
                file_name=f"{BRAND_NAME.lower()}_chat_history_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown"
            )

    # --- Quick Examples ---
    with st.expander("💡 Example Questions"):
        st.markdown("""
        - What are the top 3 categories by total sales?
        - Which columns have more than 20% missing values?
        - Show me a bar chart of average price by region
        - Is there a correlation between age and income?
        - How many unique customers are there?
        - What's the distribution of order amounts?
        - Find outliers in the 'revenue' column
        - Group sales by month and show trend line
        """)


def _generate_response(prompt: str, df: pd.DataFrame, use_llm: bool) -> Dict:
    """
    Generate response using hybrid engine:
    1. Rule-based parser (fast, reliable)
    2. Fallback to LLM if enabled and rule-based fails
    """
    try:
        # Step 1: Try rule-based engine first
        response = _parse_natural_language(prompt, df)
        if response.get("success"):
            return response

        # Step 2: If rule-based fails and LLM is enabled → call LLM
        if use_llm:
            llm_response = _query_llm(prompt, df)
            if llm_response:
                provider_name = SUPPORTED_PROVIDERS.get(st.session_state.get("llm_provider", "openai"), {}).get("name", "LLM")
                return {
                    "success": True,
                    "type": "llm",
                    "content": llm_response,
                    "source": f"LLM ({provider_name})"
                }

        # Step 3: Fallback if nothing works
        return {
            "success": False,
            "type": "error",
            "content": (
                "I couldn't understand your question. Try asking about:\n"
                "- Missing values\n"
                "- Averages or totals by category\n"
                "- Charts like 'bar', 'line', 'histogram'\n"
                "- Correlations\n"
                "Example: 'Show average sales by region'"
            ),
            "source": "Small Brain (fallback)"
        }

    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return {
            "success": False,
            "type": "error",
            "content": f"❌ Something went wrong: {str(e)}",
            "source": "System Error"
        }


def _parse_natural_language(prompt: str, df: pd.DataFrame) -> Dict:
    """
    Rule-based parser for common data queries.
    Returns structured response with type, content, and optional chart.
    """
    prompt_lower = prompt.lower().strip()
    result = {"success": False, "type": "text", "content": "", "chart": None, "table": None}

    # --- 1. Missing Values ---
    if any(k in prompt_lower for k in ["null", "missing", "na", "empty"]):
        miss = df.isnull().sum()
        top_miss = miss[miss > 0].sort_values(ascending=False).head(10)
        if len(top_miss) == 0:
            result["content"] = "✅ No missing values detected in your dataset."
        else:
            result["type"] = "data"
            result["table"] = top_miss.to_frame("Missing Count")
            result["content"] = f"🔍 Found {len(top_miss)} columns with missing values:"
        result["success"] = True
        return result

    # --- 2. Unique Values ---
    if "unique" in prompt_lower:
        uniq = df.nunique(dropna=False).sort_values(ascending=False)
        result["type"] = "data"
        result["table"] = uniq.to_frame("Unique Values")
        result["content"] = "🔢 Unique values per column:"
        result["success"] = True
        return result

    # --- 3. Numeric Summary (mean, median, etc.) ---
    if any(k in prompt_lower for k in ["mean", "average", "median", "min", "max", "sum", "count"]) and "by" not in prompt_lower:
        num_cols = get_numeric_columns(df)
        if len(num_cols) == 0:
            result["content"] = "⚠️ No numeric columns found to compute statistics."
            result["success"] = True
            return result

        agg_map = {
            "mean": "mean", "average": "mean",
            "median": "median", "min": "min", "max": "max",
            "sum": "sum", "count": "count"
        }
        target_agg = None
        for word, func in agg_map.items():
            if word in prompt_lower:
                target_agg = func
                break

        if target_agg:
            stats = getattr(df[num_cols], target_agg)().round(3)
            result["type"] = "data"
            result["table"] = stats.to_frame(target_agg.title())
            result["content"] = f"📊 {target_agg.title()} of numeric columns:"
            result["success"] = True
            return result

    # --- 4. GROUP-BY Queries: "avg of X by Y" ---
    if " by " in prompt_lower and any(k in prompt_lower for k in ["mean", "average", "median", "min", "max", "sum", "count"]):
        # Extract aggregation function
        agg_map = {
            "mean": "mean", "average": "mean",
            "median": "median", "min": "min", "max": "max",
            "sum": "sum", "count": "count"
        }
        agg_func = None
        for word, func in agg_map.items():
            if word in prompt_lower:
                agg_func = func
                break

        if not agg_func:
            return result

        # Extract Y (numeric) and X (categorical)
        cols_in_prompt = [col for col in df.columns if col.lower() in prompt_lower]
        
        y_col = None
        x_col = None
        
        # Look for column names mentioned in prompt
        for col in cols_in_prompt:
            if pd.api.types.is_numeric_dtype(df[col]) and y_col is None:
                y_col = col
            elif not pd.api.types.is_numeric_dtype(df[col]) and x_col is None:
                x_col = col

        # Fallback: auto-select best candidates
        if y_col is None:
            num_cols = get_numeric_columns(df)
            if len(num_cols) > 0:
                y_col = num_cols[0]  # First numeric
        if x_col is None:
            cat_cols = get_categorical_columns(df)
            if len(cat_cols) > 0:
                x_col = cat_cols[0]  # First categorical

        if x_col and y_col:
            try:
                if agg_func == "count":
                    grouped = df.groupby(x_col).size().reset_index(name="Count")
                else:
                    grouped = getattr(df.groupby(x_col)[y_col], agg_func)().reset_index(name=y_col.title())

                result["type"] = "frame"
                result["table"] = grouped
                result["content"] = f"📈 {agg_func.title()} of '{y_col}' by '{x_col}':"

                # Auto-generate chart
                if len(grouped) <= MAX_ROWS_FOR_PLOT:
                    if agg_func in ["mean", "sum", "count"]:
                        result["chart"] = px.bar(grouped, x=x_col, y=y_col.title(), title=f"{agg_func.title()} of {y_col} by {x_col}")
                    elif agg_func == "median":
                        result["chart"] = px.box(df, x=x_col, y=y_col, title=f"Median Distribution of {y_col} by {x_col}")
                result["success"] = True
                return result
            except Exception as e:
                logger.debug(f"Group-by failed: {e}")

    # --- 5. Chart Requests: "show histogram of X" ---
    if any(k in prompt_lower for k in ["histogram", "distribution", "density", "spread"]):
        num_cols = get_numeric_columns(df)
        if len(num_cols) == 0:
            result["content"] = "⚠️ No numeric columns to create a histogram."
            result["success"] = True
            return result

        # Extract column name
        col = None
        for c in num_cols:
            if c.lower() in prompt_lower:
                col = c
                break
        if col is None:
            col = num_cols[0]  # Fallback

        result["type"] = "chart"
        result["chart"] = px.histogram(df, x=col, nbins=30, title=f"Distribution of {col}")
        result["content"] = f"📊 Histogram for {col}:"
        result["success"] = True
        return result

    # --- 6. Correlation Heatmap ---
    if "correlation" in prompt_lower or "correlate" in prompt_lower:
        num_cols = get_numeric_columns(df)
        if len(num_cols) < 2:
            result["content"] = "⚠️ Need at least 2 numeric columns for correlation."
            result["success"] = True
            return result

        corr = df[num_cols].corr()
        result["type"] = "chart"
        result["chart"] = px.imshow(corr, color_continuous_scale='RdBu_r', zmin=-1, zmax=1, title="Correlation Heatmap")
        result["content"] = "🌡️ Correlation matrix between numeric variables:"
        result["success"] = True
        return result

    # --- 7. Top N / Bottom N ---
    if any(k in prompt_lower for k in ["top", "bottom", "highest", "lowest"]) and ("sales" in prompt_lower or "revenue" in prompt_lower or "amount" in prompt_lower):
        num_cols = get_numeric_columns(df)
        cat_cols = get_categorical_columns(df)
        if len(num_cols) == 0 or len(cat_cols) == 0:
            result["content"] = "⚠️ Need numeric and categorical columns for top/bottom queries."
            result["success"] = True
            return result

        # Assume first numeric and first categorical
        y_col = num_cols[0]
        x_col = cat_cols[0]

        # Extract "top 5", "bottom 3", etc.
        n_match = re.search(r'(top|bottom)\s*(\d+)', prompt_lower)
        n = int(n_match.group(2)) if n_match else 5
        direction = "desc" if "top" in prompt_lower or "highest" in prompt_lower else "asc"

        grouped = df.groupby(x_col)[y_col].sum().reset_index()
        sorted_df = grouped.sort_values(y_col, ascending=(direction == "asc")).tail(n) if direction == "desc" else grouped.head(n)

        result["type"] = "frame"
        result["table"] = sorted_df
        result["content"] = f"🏆 Top {n} {x_col} by {y_col}:"
        result["chart"] = px.bar(sorted_df, x=x_col, y=y_col, title=f"Top {n} {x_col} by {y_col}")
        result["success"] = True
        return result

    # --- 8. Outliers ---
    if "outlier" in prompt_lower:
        num_cols = get_numeric_columns(df)
        if len(num_cols) == 0:
            result["content"] = "⚠️ No numeric columns to detect outliers."
            result["success"] = True
            return result

        col = num_cols[0]  # Default
        for c in num_cols:
            if c.lower() in prompt_lower:
                col = c
                break

        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]

        result["type"] = "text"
        result["content"] = (
            f"⚠️ Outliers detected in `{col}`:\n"
            f"- Lower bound: {lower_bound:.2f}\n"
            f"- Upper bound: {upper_bound:.2f}\n"
            f"- Total outliers: {len(outliers):,} ({len(outliers)/len(df)*100:.1f}%)\n"
            f"- Use **Quality → Outlier Analysis** to investigate further."
        )
        result["success"] = True
        return result

    # --- 9. Count / Row Count ---
    if any(k in prompt_lower for k in ["how many", "total rows", "number of rows", "record count"]):
        result["type"] = "text"
        result["content"] = f"📌 Your dataset contains **{len(df):,} rows**."
        result["success"] = True
        return result

    # --- 10. Column Info ---
    if "columns" in prompt_lower and ("list" in prompt_lower or "what" in prompt_lower):
        result["type"] = "text"
        result["content"] = f"📋 Your dataset has {len(df.columns)} columns:\n\n" + ", ".join([f"`{c}`" for c in df.columns])
        result["success"] = True
        return result

    # --- FALLBACK: No match ---
    return result


def _query_llm(prompt: str, df: pd.DataFrame) -> Optional[str]:
    """Query LLM API with safety checks."""
    try:
        # Get provider and API key from session state
        provider = st.session_state.get("llm_provider", "openai")
        api_key = st.session_state.get(f"{provider}_api_key")
        model_name = st.session_state.get("llm_model", DEFAULT_LLM_MODEL)
        
        if not api_key:
            return f"❌ No API key provided for {SUPPORTED_PROVIDERS.get(provider, {}).get('name', provider)}. Enter it in the sidebar to use advanced AI."

        # Limit context to avoid overload
        sample_data = df.head(5).to_string(index=False)
        columns_str = ", ".join([f"`{c}` ({df[c].dtype})" for c in df.columns])

        system_prompt = f"""You are an expert data analyst assistant. 
        Answer concisely based on the dataset below.
        Do NOT make up numbers. If unsure, say "I don't know".
        
        Dataset columns: {columns_str}
        Sample rows:
        {sample_data}

        User question: {prompt}"""
        
        if provider == "openai":
            return _query_openai(api_key, model_name, system_prompt, prompt)
        elif provider == "anthropic":
            return _query_anthropic(api_key, model_name, system_prompt, prompt)
        elif provider == "google":
            return _query_google(api_key, model_name, system_prompt, prompt)
        else:
            return "❌ Unsupported LLM provider selected."
            
    except Exception as e:
        logger.error(f"LLM query error: {e}")
        return f"❌ Error querying LLM: {str(e)}"


def _query_openai(api_key: str, model_name: str, system_prompt: str, user_prompt: str) -> str:
    """Query OpenAI API (supports both legacy and new SDK styles)."""
    try:
        import openai  # type: ignore

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # New SDK style (openai>=1.x)
        if hasattr(openai, "OpenAI"):
            client = openai.OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            return completion.choices[0].message.content.strip()

        # Legacy SDK style (openai<1.x)
        if hasattr(openai, "api_key") and hasattr(openai, "ChatCompletion"):
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()

        return "❌ Unsupported OpenAI SDK version."
    except ImportError:
        return "❌ OpenAI library not installed. Install with: `pip install openai`"


def _query_anthropic(api_key: str, model_name: str, system_prompt: str, user_prompt: str) -> str:
    """Query Anthropic API"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model=model_name,
            max_tokens=1024,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.content[0].text
    except ImportError:
        return "❌ Anthropic library not installed. Install with: `pip install anthropic`"


def _query_google(api_key: str, model_name: str, system_prompt: str, user_prompt: str) -> str:
    """Query Google Gemini API"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(f"{system_prompt}\n\nUser question: {user_prompt}")
        
        return response.text
    except ImportError:
        return "❌ Google Generative AI library not installed. Install with: `pip install google-generativeai`"


def _display_response(response: Dict, is_history: bool = False) -> None:
    """Display response with appropriate formatting."""
    if not response.get("success"):
        st.error(response.get("content", "Unknown error"))
        return

    source = response.get("source", "System")
    st.markdown(f"<small><em>Source: {source}</em></small>", unsafe_allow_html=True)

    content = response.get("content", "")
    if content:
        st.markdown(content)

    # Display table if present
    table = response.get("table")
    if table is not None:
        st.dataframe(table, use_container_width=True)

    # Display chart if present
    chart = response.get("chart")
    if chart:
        st.plotly_chart(chart, use_container_width=True)

    # Add a separator if not in history view
    if not is_history:
        st.markdown("---")


def _export_chat_as_markdown(chat_history: List[Dict]) -> str:
    """Export chat history as markdown."""
    md = f"# {BRAND_NAME} Chat History\n\n"
    md += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"
    
    for i, msg in enumerate(chat_history):
        md += f"## Q{i+1}: {msg['question']}\n\n"
        response = msg['response']
        if response.get("success"):
            md += f"**Source:** {response.get('source', 'System')}\n\n"
            md += f"{response.get('content', '')}\n\n"
            
            table = response.get("table")
            if table is not None:
                md += "### Data Table\n\n"
                md += table.to_markdown(index=False) + "\n\n"
        else:
            md += f"❌ Error: {response.get('content', 'Unknown error')}\n\n"
        md += "---\n\n"
        
    return md