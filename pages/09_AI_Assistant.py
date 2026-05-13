"""
💬 AI Assistant - Multi-Provider Intelligent Data Copilot
Supports: OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, 
          Ollama, Groq, Mistral, and any OpenAI-compatible API
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="AI ASSISTANT | FINESE2", page_icon="💬", layout="wide")

from utils.session_state import SessionManager
from utils.styling import render_section_header, render_status_badge
from utils.helpers import create_data_profile_text, safe_json_dump, truncate_text
from modules.ai_assistant import AIAssistant, Message, AIResponse, PROVIDERS

SessionManager.init()

st.title("💬 AI Data Assistant")
st.caption("Your intelligent copilot for deep data analysis, modeling guidance, and insights")

# Sidebar with navigation
with st.sidebar:

    # Provider selection
    providers = AIAssistant.get_available_providers()
    provider_names = {k: f"{v['icon']} {v['name']}" for k, v in providers.items()}

    current_provider = SessionManager.get("ai_provider")
    if current_provider not in provider_names:
        current_provider = "openai"

    selected_provider = st.selectbox(
        "AI Provider",
        options=list(provider_names.keys()),
        format_func=lambda x: provider_names[x],
        index=list(provider_names.keys()).index(current_provider)
    )
    SessionManager.set("ai_provider", selected_provider)

    provider_info = providers[selected_provider]
    st.caption(f"{provider_info['description']}")

    # API Key
    api_key = st.text_input(
        "API Key",
        value=SessionManager.get("ai_api_key"),
        type="password",
        placeholder="Enter your API key...",
        help=f"Required for {provider_info['name']}"
    )
    SessionManager.set("ai_api_key", api_key)

    # Base URL (if needed)
    if provider_info.get("needs_base_url"):
        default_url = provider_info.get("default_base_url", "")
        current_url = SessionManager.get("ai_base_url") or default_url
        base_url = st.text_input(
            "Base URL",
            value=current_url,
            placeholder=default_url,
            help="Required for custom/local endpoints"
        )
        SessionManager.set("ai_base_url", base_url)

    # Model selection
    default_models = provider_info["default_models"]
    current_model = SessionManager.get("ai_model")
    if current_model not in default_models:
        current_model = default_models[0]

    model = st.selectbox(
        "Model",
        options=default_models,
        index=default_models.index(current_model) if current_model in default_models else 0
    )
    SessionManager.set("ai_model", model)

    # Advanced settings
    with st.expander("Advanced", expanded=False):
        temp = st.slider("Temperature", 0.0, 2.0, SessionManager.get("ai_temperature"), 0.1)
        SessionManager.set("ai_temperature", temp)

        max_tokens = st.slider("Max Tokens", 256, 8192, SessionManager.get("ai_max_tokens"), 256)
        SessionManager.set("ai_max_tokens", max_tokens)

        system_prompt = st.text_area(
            "System Prompt",
            value=SessionManager.get("ai_system_prompt"),
            height=100
        )
        SessionManager.set("ai_system_prompt", system_prompt)

    # Test connection
    if st.button("🔄 Test Connection", use_container_width=True):
        if not api_key and selected_provider != "ollama":
            st.error("API Key required!")
        else:
            with st.spinner("Testing..."):
                try:
                    assistant = AIAssistant(
                        provider_name=selected_provider,
                        api_key=api_key,
                        base_url=SessionManager.get("ai_base_url"),
                        model=model
                    )
                    if assistant.validate():
                        st.success(f"✅ Connected to {providers[selected_provider]['name']}!")
                    else:
                        st.error("❌ Connection failed")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    st.markdown("---")

    # Data context toggle
    include_data = st.toggle("📊 Include Data Context", value=True,
                            help="Send dataset schema and summary to AI for context-aware responses")

    include_sample = st.toggle("👁️ Include Sample Rows", value=False,
                              help="Send first 5 rows of data (use with caution on sensitive data)")

    st.markdown("---")

    if st.button("🗑️ Clear Chat History", use_container_width=True, type="secondary"):
        SessionManager.set("chat_history", [])
        st.rerun()

    st.caption("v1.0.0 | data_all1")

# ==================== MAIN CHAT INTERFACE ====================

# Initialize assistant
assistant = None
try:
    assistant = AIAssistant(
        provider_name=selected_provider,
        api_key=api_key,
        base_url=SessionManager.get("ai_base_url"),
        model=model
    )
except Exception as e:
    st.error(f"Failed to initialize AI assistant: {str(e)}")

# Build system message with data context
def build_system_message() -> str:
    base_prompt = SessionManager.get("ai_system_prompt")

    if not include_data or not SessionManager.has_data():
        return base_prompt

    df = SessionManager.get_df()
    data_profile = create_data_profile_text(df)

    context = f"""
{base_prompt}

CURRENT DATASET CONTEXT:
{data_profile}
"""

    if include_sample and df is not None:
        sample = df.head(5).to_string()
        context += "\n\nSAMPLE DATA (first 5 rows):\n{sample}".format(sample=sample)

    context += """

INSTRUCTIONS FOR RESPONSES:
- Provide actionable, data-driven insights
- When suggesting analysis, be specific about which columns to use
- For modeling suggestions, mention appropriate algorithms and preprocessing steps
- Use code formatting for clarity
- If asked to write code, provide clean, well-commented Python
- Always consider data quality issues (missing values, outliers, skewness) in your recommendations
"""
    return context

# Display chat history
st.markdown("""
<style>
.chat-container {
    max-height: 600px;
    overflow-y: auto;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

chat_history = SessionManager.get("chat_history")

# Welcome message if empty
if not chat_history:
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; background: #1C1F26; border-radius: 12px; border: 1px solid #2A2D35;">
        <div style="font-size: 3rem; margin-bottom: 15px;">🤖</div>
        <h3 style="color: #00D4AA; margin-bottom: 10px;">Welcome to AI Data Assistant</h3>
        <p style="color: #888; max-width: 500px; margin: 0 auto; line-height: 1.6;">
            Ask me anything about your data! I can help with:<br><br>
        </p>
    </div>
    """, unsafe_allow_html=True)

# Render chat messages
for msg in chat_history:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])

            # Show metadata if available
            if msg.get("model"):
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.caption(f"🤖 {msg.get('provider', 'AI')} · {truncate_text(msg.get('model', ''), 20)}")
                with col2:
                    if msg.get("usage"):
                        usage = msg["usage"]
                        st.caption(f"Tokens: {usage.get('total_tokens', 'N/A')} | {msg.get('timestamp', '')}")

# Chat input
st.markdown("<br>", unsafe_allow_html=True)

# Suggested prompts
if not chat_history:
    st.markdown("**Quick Prompts:**")
    cols = st.columns(4)
    suggestions = [
        "📊 Summarize the key insights from this dataset",
        "🧹 What cleaning steps do you recommend?",
        "🤖 Suggest the best ML model for this data",
        "📈 Analyze correlations and relationships"
    ]

    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, use_container_width=True, key=f"suggest_{i}"):
                st.session_state["chat_input"] = suggestion.replace("📊 ", "").replace("🧹 ", "").replace("🤖 ", "").replace("📈 ", "")
                st.rerun()

# Input area
prompt = st.chat_input("💬 Ask me about your data...", key="chat_input")

if prompt and assistant:
    # Add user message
    chat_history.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    SessionManager.set("chat_history", chat_history)

    # Build messages for API
    messages = [Message(role="system", content=build_system_message())]

    # Add recent chat history (last 10 messages)
    for msg in chat_history[-10:]:
        messages.append(Message(role=msg["role"], content=msg["content"]))

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        response_placeholder = st.empty()

        try:
            with st.spinner(f"Thinking with {provider_info['name']}..."):
                # Try streaming first
                try:
                    response_stream = assistant.chat(
                        messages=messages,
                        stream=True,
                        temperature=SessionManager.get("ai_temperature"),
                        max_tokens=SessionManager.get("ai_max_tokens")
                    )

                    full_response = ""
                    for chunk in response_stream:
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")

                    response_placeholder.markdown(full_response)

                    # For streaming, we don't get usage stats
                    ai_response = {
                        "role": "assistant",
                        "content": full_response,
                        "provider": selected_provider,
                        "model": model,
                        "usage": {},
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }

                except Exception as stream_error:
                    # Fallback to non-streaming
                    response = assistant.chat(
                        messages=messages,
                        stream=False,
                        temperature=SessionManager.get("ai_temperature"),
                        max_tokens=SessionManager.get("ai_max_tokens")
                    )

                    full_response = response.content
                    response_placeholder.markdown(full_response)

                    ai_response = {
                        "role": "assistant",
                        "content": full_response,
                        "provider": selected_provider,
                        "model": response.model,
                        "usage": response.usage,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }

                # Add to history
                chat_history.append(ai_response)
                SessionManager.set("chat_history", chat_history)

                # Show metadata
                with st.expander("Response Details", expanded=False):
                    st.json({
                        "provider": selected_provider,
                        "model": model,
                        "timestamp": ai_response["timestamp"],
                        "usage": ai_response.get("usage", {})
                    })

        except Exception as e:
            error_msg = f"**Error:** {str(e)}\n\nPlease check your API key and connection settings."
            response_placeholder.error(error_msg)

            chat_history.append({
                "role": "assistant",
                "content": error_msg,
                "provider": selected_provider,
                "model": model,
                "error": True,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            SessionManager.set("chat_history", chat_history)

# Data context panel (collapsible)
if SessionManager.has_data() and include_data:
    with st.expander("📊 Current Data Context (sent to AI)", expanded=False):
        df = SessionManager.get_df()
        st.text(create_data_profile_text(df))