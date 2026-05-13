"""
AI Assistant Module - Unified Multi-Provider Interface
Supports: OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, 
          Ollama (local), Groq, Mistral, and any OpenAI-compatible API
"""
import os
import json
import base64
import io
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator, Union
from dataclasses import dataclass, field
import streamlit as st
import traceback

# Provider imports (lazy loaded to avoid hard dependencies)
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


@dataclass
class Message:
    """Standardized message format across all providers."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    images: Optional[List[str]] = field(default_factory=list)  # base64 encoded images


@dataclass
class AIResponse:
    """Standardized response format."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Any = None


class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.extra_params = kwargs

    @abstractmethod
    def chat(self, messages: List[Message], model: str, temperature: float = 0.7, 
             max_tokens: int = 4096, stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:
        """Send chat completion request."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate API key and connection."""
        pass

    def _messages_to_provider_format(self, messages: List[Message]) -> List[Dict]:
        """Convert standardized messages to provider-specific format. Override if needed."""
        return [{"role": m.role, "content": m.content} for m in messages if m.role != "system" or self.__class__.__name__ != "OpenAIProvider"]


class OpenAIProvider(BaseProvider):
    """OpenAI and OpenAI-compatible providers (Groq, Mistral, LocalAI, etc.)"""

    DEFAULT_MODELS = [
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",
        "o1-preview", "o1-mini", "o3-mini"
    ]

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        if openai is None:
            raise ImportError("openai package not installed. Run: pip install openai")

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**client_kwargs)

    def chat(self, messages: List[Message], model: str, temperature: float = 0.7,
             max_tokens: int = 4096, stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:

        # Handle system message
        formatted_msgs = []
        system_content = ""
        for m in messages:
            if m.role == "system":
                system_content = m.content
            else:
                formatted_msgs.append({"role": m.role, "content": m.content})

        # For o1 models, system message goes in developer role or first user message
        if model.startswith("o1") or model.startswith("o3"):
            if system_content:
                formatted_msgs.insert(0, {"role": "developer", "content": system_content})
        else:
            if system_content:
                formatted_msgs.insert(0, {"role": "system", "content": system_content})

        params = {
            "model": model,
            "messages": formatted_msgs,
            "max_tokens": max_tokens,
            **kwargs
        }

        # o1 models don't support temperature
        if not (model.startswith("o1") or model.startswith("o3")):
            params["temperature"] = temperature

        if stream:
            params["stream"] = True
            try:
                response = self.client.chat.completions.create(**params)
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e:
                st.error(f"Error during streaming: {str(e)}")
                traceback.print_exc()
                raise
        else:
            try:
                response = self.client.chat.completions.create(**params)
                return AIResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    provider="openai",
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
                    },
                    finish_reason=response.choices[0].finish_reason,
                    raw_response=response
                )
            except Exception as e:
                st.error(f"Error during OpenAI request: {str(e)}")
                traceback.print_exc()
                raise

    def list_models(self) -> List[str]:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data if "gpt" in m.id or "o1" in m.id or "o3" in m.id]
        except Exception as e:
            st.warning(f"Could not list models: {str(e)}")
            return self.DEFAULT_MODELS

    def validate(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception as e:
            st.error(f"OpenAI validation failed: {str(e)}")
            return False


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""

    DEFAULT_MODELS = [
        "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229", "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        if anthropic is None:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = anthropic.Anthropic(**client_kwargs)

    def chat(self, messages: List[Message], model: str, temperature: float = 0.7,
             max_tokens: int = 4096, stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:

        system_msg = ""
        formatted_msgs = []

        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                formatted_msgs.append({"role": m.role, "content": m.content})

        params = {
            "model": model,
            "messages": formatted_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        if system_msg:
            params["system"] = system_msg

        if stream:
            params["stream"] = True
            try:
                with self.client.messages.stream(**params) as stream_resp:
                    for text in stream_resp.text_stream:
                        yield text
            except Exception as e:
                st.error(f"Error during Anthropic streaming: {str(e)}")
                traceback.print_exc()
                raise
        else:
            try:
                response = self.client.messages.create(**params)
                return AIResponse(
                    content=response.content[0].text if response.content else "",
                    model=response.model,
                    provider="anthropic",
                    usage={
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    finish_reason=response.stop_reason,
                    raw_response=response
                )
            except Exception as e:
                st.error(f"Error during Anthropic request: {str(e)}")
                traceback.print_exc()
                raise

    def list_models(self) -> List[str]:
        return self.DEFAULT_MODELS

    def validate(self) -> bool:
        try:
            self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            st.error(f"Anthropic validation failed: {str(e)}")
            return False


class GoogleProvider(BaseProvider):
    """Google Gemini provider."""

    DEFAULT_MODELS = [
        "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-pro-exp-0827", "gemini-1.5-pro-vision-exp-1114",
        "gemini-1.0-pro", "gemini-1.0-pro-vision"
    ]

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        if genai is None:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        genai.configure(api_key=api_key)

    def chat(self, messages: List[Message], model: str, temperature: float = 0.7,
             max_tokens: int = 4096, stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:

        system_msg = ""
        history = []

        for m in messages:
            if m.role == "system":
                system_msg = m.content
            elif m.role == "user":
                history.append({"role": "user", "parts": [m.content]})
            elif m.role == "assistant":
                history.append({"role": "model", "parts": [m.content]})

        try:
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_msg if system_msg else None
            )

            # Separate last user message from history
            if history and history[-1]["role"] == "user":
                last_msg = history.pop()["parts"][0]
            else:
                last_msg = "Hello"

            chat = gemini_model.start_chat(history=history)

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                **kwargs
            )

            if stream:
                response = chat.send_message(last_msg, generation_config=generation_config, stream=True)
                for chunk in response:
                    if hasattr(chunk, 'text'):
                        yield chunk.text
            else:
                response = chat.send_message(last_msg, generation_config=generation_config)
                # Ensure the response has the expected attributes
                content_text = ""
                if hasattr(response, 'text'):
                    content_text = response.text
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    # Extract text from the first candidate's content parts
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                content_text = part.text
                                break

                return AIResponse(
                    content=content_text,
                    model=model,
                    provider="google",
                    usage={
                        "prompt_tokens": getattr(response, 'usage_metadata', {}).get('prompt_token_count', 0),
                        "completion_tokens": getattr(response, 'usage_metadata', {}).get('candidate_token_count', 0),
                        "total_tokens": getattr(response, 'usage_metadata', {}).get('total_token_count', 0)
                    } if hasattr(response, 'usage_metadata') else {},
                    finish_reason=getattr(response, 'candidates', [{}])[0].get('finish_reason', None) if hasattr(response, 'candidates') and len(response.candidates) > 0 else None,
                    raw_response=response
                )
        except Exception as e:
            st.error(f"Error during Google Gemini request: {str(e)}")
            traceback.print_exc()
            raise

    def list_models(self) -> List[str]:
        try:
            models = genai.list_models()
            return [m.name.replace("models/", "") for m in models if "gemini" in m.name]
        except Exception as e:
            st.warning(f"Could not list Google models: {str(e)}")
            return self.DEFAULT_MODELS

    def validate(self) -> bool:
        try:
            genai.list_models()
            return True
        except Exception as e:
            st.error(f"Google Gemini validation failed: {str(e)}")
            return False


class OllamaProvider(BaseProvider):
    """Ollama local model provider - OpenAI-compatible API."""

    DEFAULT_MODELS = [
        "llama3.2", "llama3.1", "llama3", "mistral", "codellama",
        "phi4", "phi3", "gemma2", "qwen2.5", "deepseek-r1"
    ]

    def __init__(self, api_key: str = "ollama", base_url: str = "http://localhost:11434/v1", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        if openai is None:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)

    def chat(self, messages: List[Message], model: str, temperature: float = 0.7,
             max_tokens: int = 4096, stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:

        formatted_msgs = [{"role": m.role, "content": m.content} for m in messages]

        params = {
            "model": model,
            "messages": formatted_msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        if stream:
            params["stream"] = True
            try:
                response = self.client.chat.completions.create(**params)
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e:
                st.error(f"Error during Ollama streaming: {str(e)}")
                traceback.print_exc()
                raise
        else:
            try:
                response = self.client.chat.completions.create(**params)
                return AIResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    provider="ollama",
                    usage={},
                    finish_reason=response.choices[0].finish_reason,
                    raw_response=response
                )
            except Exception as e:
                st.error(f"Error during Ollama request: {str(e)}")
                traceback.print_exc()
                raise

    def list_models(self) -> List[str]:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            st.warning(f"Could not list Ollama models: {str(e)}")
            return self.DEFAULT_MODELS

    def validate(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception as e:
            st.error(f"Ollama validation failed: {str(e)}")
            return False


class AzureOpenAIProvider(OpenAIProvider):
    """Azure OpenAI Service provider."""

    def __init__(self, api_key: str, base_url: str, **kwargs):
        # Azure requires base_url with api-version
        super().__init__(api_key, base_url, **kwargs)
        self.api_version = kwargs.get("api_version", "2024-10-21")
        # Re-init client with Azure-specific settings
        self.client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=base_url,
            api_version=self.api_version
        )

    def list_models(self) -> List[str]:
        return ["gpt-4o", "gpt-4", "gpt-35-turbo"]


# Provider Registry
PROVIDERS = {
    "openai": {
        "class": OpenAIProvider,
        "name": "OpenAI",
        "icon": "🟢",
        "default_models": OpenAIProvider.DEFAULT_MODELS,
        "needs_base_url": False,
        "description": "OpenAI GPT models"
    },
    "anthropic": {
        "class": AnthropicProvider,
        "name": "Anthropic Claude",
        "icon": "🟣",
        "default_models": AnthropicProvider.DEFAULT_MODELS,
        "needs_base_url": False,
        "description": "Claude 3.5 Sonnet, Opus, Haiku"
    },
    "google": {
        "class": GoogleProvider,
        "name": "Google Gemini",
        "icon": "🔵",
        "default_models": GoogleProvider.DEFAULT_MODELS,
        "needs_base_url": False,
        "description": "Gemini 1.5 Pro & Flash"
    },
    "azure": {
        "class": AzureOpenAIProvider,
        "name": "Azure OpenAI",
        "icon": "☁️",
        "default_models": ["gpt-4o", "gpt-4", "gpt-35-turbo"],
        "needs_base_url": True,
        "description": "Azure OpenAI Service"
    },
    "ollama": {
        "class": OllamaProvider,
        "name": "Ollama (Local)",
        "icon": "🏠",
        "default_models": OllamaProvider.DEFAULT_MODELS,
        "needs_base_url": True,
        "default_base_url": "http://localhost:11434/v1",
        "description": "Local models via Ollama"
    },
    "groq": {
        "class": OpenAIProvider,
        "name": "Groq",
        "icon": "⚡",
        "default_models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma-7b-it"],
        "needs_base_url": True,
        "default_base_url": "https://api.groq.com/openai/v1",
        "description": "Ultra-fast inference via Groq"
    },
    "mistral": {
        "class": OpenAIProvider,
        "name": "Mistral AI",
        "icon": "🌫️",
        "default_models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "codestral-latest"],
        "needs_base_url": True,
        "default_base_url": "https://api.mistral.ai/v1",
        "description": "Mistral models"
    },
    "custom": {
        "class": OpenAIProvider,
        "name": "Custom (OpenAI-compatible)",
        "icon": "🔧",
        "default_models": ["custom-model"],
        "needs_base_url": True,
        "default_base_url": "http://localhost:8000/v1",
        "description": "Any OpenAI-compatible endpoint"
    }
}


class AIAssistant:
    """Unified AI Assistant that works with any configured provider."""

    def __init__(self, provider_name: str = "openai", api_key: str = "", 
                 base_url: str = "", model: str = "", **kwargs):
        self.provider_name = provider_name
        self.provider_config = PROVIDERS.get(provider_name, PROVIDERS["openai"])

        # Auto-set base_url for providers that need it
        if not base_url and self.provider_config.get("needs_base_url"):
            base_url = self.provider_config.get("default_base_url", "")

        # Auto-set model if not provided
        if not model:
            model = self.provider_config["default_models"][0]

        self.model = model
        self.base_url = base_url

        # Initialize provider
        provider_class = self.provider_config["class"]
        self.provider = provider_class(api_key=api_key, base_url=base_url, **kwargs)

    def chat(self, messages: List[Message], stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:
        """Send chat request to the configured provider."""
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)

        return self.provider.chat(
            messages=messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
        )

    def validate(self) -> bool:
        """Check if the provider connection works."""
        try:
            return self.provider.validate()
        except Exception as e:
            st.error(f"Error validating provider: {str(e)}")
            traceback.print_exc()
            return False

    def list_models(self) -> List[str]:
        """List available models for this provider."""
        try:
            return self.provider.list_models()
        except Exception as e:
            st.error(f"Error listing models: {str(e)}")
            traceback.print_exc()
            return []

    @staticmethod
    def get_available_providers() -> Dict[str, Dict]:
        """Get all available provider configurations."""
        return PROVIDERS

    @staticmethod
    def create_from_session() -> "AIAssistant":
        """Factory method to create assistant from Streamlit session state."""
        from utils.session_state import SessionManager

        provider = SessionManager.get("ai_provider")
        api_key = SessionManager.get("ai_api_key")
        base_url = SessionManager.get("ai_base_url")
        model = SessionManager.get("ai_model")

        return AIAssistant(
            provider_name=provider,
            api_key=api_key,
            base_url=base_url,
            model=model
        )
    
def render_ai_settings_sidebar():
    """Render AI provider settings in the sidebar. Call this on every page."""
    from utils.session_state import SessionManager
    from utils.helpers import create_data_profile_text

    with st.sidebar:
        with st.expander("🤖 AI Assistant Settings", expanded=False):
            providers = AIAssistant.get_available_providers()
            provider_names = {k: f"{v['icon']} {v['name']}" for k, v in providers.items()}

            selected_provider = st.selectbox(
                "Provider",
                options=list(provider_names.keys()),
                format_func=lambda x: provider_names[x],
                index=list(provider_names.keys()).index(SessionManager.get("ai_provider"))
            )
            SessionManager.set("ai_provider", selected_provider)

            # API Key
            api_key = st.text_input(
                "API Key",
                value=SessionManager.get("ai_api_key"),
                type="password",
                placeholder="sk-..." if selected_provider == "openai" else "...",
                help=f"Your {providers[selected_provider]['name']} API key"
            )
            SessionManager.set("ai_api_key", api_key)

            # Base URL (if needed)
            if providers[selected_provider].get("needs_base_url"):
                base_url = st.text_input(
                    "Base URL (Optional)",
                    value=SessionManager.get("ai_base_url") or providers[selected_provider].get("default_base_url", ""),
                    placeholder=providers[selected_provider].get("default_base_url", "")
                )
                SessionManager.set("ai_base_url", base_url)

            # Model selection
            default_models = providers[selected_provider]["default_models"]
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