"""
AI Assistant Module - Unified Multi-Provider Interface
Supports: OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, 
          Ollama (local), Groq, Mistral, and any OpenAI-compatible API
Refactored: No Streamlit dependencies
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator, Union
from dataclasses import dataclass, field
import traceback

logger = logging.getLogger(__name__)

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
    import google.genai as genai
except ImportError:
    genai = None


@dataclass
class Message:
    """Standardized message format across all providers."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    images: Optional[List[str]] = field(default_factory=list)


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
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        pass

    @abstractmethod
    def validate(self) -> bool:
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI and OpenAI-compatible providers."""

    DEFAULT_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

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
        formatted_msgs = []
        system_content = ""
        for m in messages:
            if m.role == "system":
                system_content = m.content
            else:
                formatted_msgs.append({"role": m.role, "content": m.content})

        if system_content:
            formatted_msgs.insert(0, {"role": "system", "content": system_content})

        params = {"model": model, "messages": formatted_msgs, "max_tokens": max_tokens, **kwargs}
        if not (model.startswith("o1") or model.startswith("o3")):
            params["temperature"] = temperature

        if stream:
            params["stream"] = True
            response = self.client.chat.completions.create(**params)
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = self.client.chat.completions.create(**params)
            return AIResponse(
                content=response.choices[0].message.content,
                model=response.model, provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                finish_reason=response.choices[0].finish_reason, raw_response=response
            )

    def list_models(self) -> List[str]:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data if "gpt" in m.id]
        except Exception:
            return self.DEFAULT_MODELS

    def validate(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""

    DEFAULT_MODELS = ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        if anthropic is None:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        self.client = anthropic.Anthropic(api_key=api_key)

    def chat(self, messages: List[Message], model: str, temperature: float = 0.7,
             max_tokens: int = 4096, stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:
        system_msg = ""
        formatted_msgs = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                formatted_msgs.append({"role": m.role, "content": m.content})

        params = {"model": model, "messages": formatted_msgs, "max_tokens": max_tokens, "temperature": temperature, **kwargs}
        if system_msg:
            params["system"] = system_msg

        if stream:
            params["stream"] = True
            with self.client.messages.stream(**params) as stream_resp:
                for text in stream_resp.text_stream:
                    yield text
        else:
            response = self.client.messages.create(**params)
            return AIResponse(
                content=response.content[0].text if response.content else "",
                model=response.model, provider="anthropic",
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                finish_reason=response.stop_reason, raw_response=response
            )

    def list_models(self) -> List[str]:
        return self.DEFAULT_MODELS

    def validate(self) -> bool:
        try:
            self.client.messages.create(model="claude-3-haiku-20240307", max_tokens=10, messages=[{"role": "user", "content": "Hi"}])
            return True
        except Exception:
            return False


class GoogleProvider(BaseProvider):
    """Google Gemini provider."""

    DEFAULT_MODELS = ["gemini-1.5-pro", "gemini-1.5-flash"]

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

        gemini_model = genai.GenerativeModel(model_name=model, system_instruction=system_msg if system_msg else None)
        last_msg = history.pop()["parts"][0] if history and history[-1]["role"] == "user" else "Hello"
        chat = gemini_model.start_chat(history=history)

        generation_config = genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens, **kwargs)

        if stream:
            response = chat.send_message(last_msg, generation_config=generation_config, stream=True)
            for chunk in response:
                if hasattr(chunk, 'text'):
                    yield chunk.text
        else:
            response = chat.send_message(last_msg, generation_config=generation_config)
            content_text = response.text if hasattr(response, 'text') else ""
            return AIResponse(
                content=content_text, model=model, provider="google",
                usage=getattr(response, 'usage_metadata', {}),
                raw_response=response
            )

    def list_models(self) -> List[str]:
        try:
            models = genai.list_models()
            return [m.name.replace("models/", "") for m in models if "gemini" in m.name]
        except Exception:
            return self.DEFAULT_MODELS

    def validate(self) -> bool:
        try:
            genai.list_models()
            return True
        except Exception:
            return False


class OllamaProvider(BaseProvider):
    """Ollama local model provider."""

    DEFAULT_MODELS = ["llama3.2", "llama3.1", "mistral", "phi4", "gemma2", "qwen2.5"]

    def __init__(self, api_key: str = "ollama", base_url: str = "http://localhost:11434/v1", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        if openai is None:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)

    def chat(self, messages: List[Message], model: str, temperature: float = 0.7,
             max_tokens: int = 4096, stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:
        formatted_msgs = [{"role": m.role, "content": m.content} for m in messages]
        params = {"model": model, "messages": formatted_msgs, "temperature": temperature, "max_tokens": max_tokens, **kwargs}

        if stream:
            params["stream"] = True
            response = self.client.chat.completions.create(**params)
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = self.client.chat.completions.create(**params)
            return AIResponse(
                content=response.choices[0].message.content,
                model=response.model, provider="ollama",
                usage={}, finish_reason=response.choices[0].finish_reason, raw_response=response
            )

    def list_models(self) -> List[str]:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return self.DEFAULT_MODELS

    def validate(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False


# Provider Registry
PROVIDERS = {
    "openai": {"class": OpenAIProvider, "name": "OpenAI", "icon": "🟢", "default_models": OpenAIProvider.DEFAULT_MODELS, "needs_base_url": False},
    "anthropic": {"class": AnthropicProvider, "name": "Anthropic Claude", "icon": "🟣", "default_models": AnthropicProvider.DEFAULT_MODELS, "needs_base_url": False},
    "google": {"class": GoogleProvider, "name": "Google Gemini", "icon": "🔵", "default_models": GoogleProvider.DEFAULT_MODELS, "needs_base_url": False},
    "ollama": {"class": OllamaProvider, "name": "Ollama (Local)", "icon": "🏠", "default_models": OllamaProvider.DEFAULT_MODELS, "needs_base_url": True, "default_base_url": "http://localhost:11434/v1"},
    "groq": {"class": OpenAIProvider, "name": "Groq", "icon": "⚡", "default_models": ["llama-3.1-70b-versatile", "mixtral-8x7b-32768"], "needs_base_url": True, "default_base_url": "https://api.groq.com/openai/v1"},
    "mistral": {"class": OpenAIProvider, "name": "Mistral AI", "icon": "🌫️", "default_models": ["mistral-large-latest", "mistral-small-latest"], "needs_base_url": True, "default_base_url": "https://api.mistral.ai/v1"},
    "custom": {"class": OpenAIProvider, "name": "Custom (OpenAI-compatible)", "icon": "🔧", "default_models": ["custom-model"], "needs_base_url": True, "default_base_url": "http://localhost:8000/v1"},
}


class AIAssistant:
    """Unified AI Assistant that works with any configured provider."""

    def __init__(self, provider_name: str = "openai", api_key: str = "",
                 base_url: str = "", model: str = "", **kwargs):
        self.provider_name = provider_name
        self.provider_config = PROVIDERS.get(provider_name, PROVIDERS["openai"])

        if not base_url and self.provider_config.get("needs_base_url"):
            base_url = self.provider_config.get("default_base_url", "")

        if not model:
            model = self.provider_config["default_models"][0]

        self.model = model
        self.base_url = base_url

        provider_class = self.provider_config["class"]
        self.provider = provider_class(api_key=api_key, base_url=base_url, **kwargs)

    def chat(self, messages: List[Message], stream: bool = False, **kwargs) -> Union[AIResponse, Generator[str, None, None]]:
        """Send chat request to the configured provider."""
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)
        return self.provider.chat(
            messages=messages, model=self.model, temperature=temperature,
            max_tokens=max_tokens, stream=stream,
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
        )

    def validate(self) -> bool:
        """Check if the provider connection works."""
        try:
            return self.provider.validate()
        except Exception as e:
            logger.error(f"Error validating provider: {str(e)}")
            return False

    def list_models(self) -> List[str]:
        """List available models for this provider."""
        try:
            return self.provider.list_models()
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []

    @staticmethod
    def get_available_providers() -> Dict[str, Dict]:
        """Get all available provider configurations."""
        return PROVIDERS
