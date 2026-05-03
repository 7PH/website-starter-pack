# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
LLM integration helper using LiteLLM.
Provides unified interface for LLM completions across multiple providers.
"""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager

from fastapi import HTTPException

from ..constants import LLM_API_BASE, LLM_API_KEY, LLM_ENABLED, LLM_MODEL, LLM_PROVIDER

logger = logging.getLogger(__name__)


def init_llm() -> None:
    """Initialize LLM with API keys. Call this at app startup."""
    if not LLM_ENABLED:
        logger.info("LLM integration disabled")
        return

    # LiteLLM looks up keys by provider-specific env var name
    # (ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, ...).
    # Mirror LLM_API_KEY into the slot LiteLLM expects.
    if LLM_API_KEY:
        os.environ[f"{LLM_PROVIDER.upper()}_API_KEY"] = LLM_API_KEY

    if LLM_API_BASE and LLM_PROVIDER == "azure":
        os.environ["AZURE_API_BASE"] = LLM_API_BASE

    logger.info(f"LLM initialized with provider={LLM_PROVIDER}, model={LLM_MODEL}")


def is_enabled() -> bool:
    """Check if LLM is configured and enabled."""
    return LLM_ENABLED


def get_model_name(model: str | None = None) -> str:
    """
    Get the full model name for LiteLLM.

    LiteLLM uses prefixes to identify providers:
    - anthropic/claude-3-opus -> Anthropic
    - openai/gpt-4 -> OpenAI
    - ollama/llama2 -> Ollama
    - azure/deployment-name -> Azure
    """
    base_model = model or LLM_MODEL

    # If model already has a provider prefix, use as-is
    if "/" in base_model:
        return base_model

    # Provider prefix mapping - some providers don't need prefixes
    provider_prefixes = {
        "openai": "",  # OpenAI models don't need prefix
        "anthropic": "",  # Anthropic models don't need prefix
        "ollama": "ollama/",
        "azure": "azure/",
    }

    prefix = provider_prefixes.get(LLM_PROVIDER, f"{LLM_PROVIDER}/")
    return f"{prefix}{base_model}" if prefix else base_model


def _convert_messages(messages: list) -> list[dict]:
    """Convert messages to dict format if they're Pydantic models."""
    result = []
    for msg in messages:
        if hasattr(msg, "model_dump"):
            result.append(msg.model_dump())
        elif isinstance(msg, dict):
            result.append(msg)
        else:
            result.append({"role": str(msg.role), "content": str(msg.content)})
    return result


def _build_completion_kwargs(messages: list, model: str | None, *, stream: bool = False) -> dict:
    kwargs: dict = {
        "model": get_model_name(model),
        "messages": _convert_messages(messages),
    }
    if stream:
        kwargs["stream"] = True
    if LLM_API_BASE and LLM_PROVIDER in ("ollama", "azure"):
        kwargs["api_base"] = LLM_API_BASE
    return kwargs


@contextmanager
def _llm_available():
    """Gate calls on ``LLM_ENABLED`` and translate litellm/import failures to HTTPException."""
    if not LLM_ENABLED:
        raise HTTPException(status_code=503, detail="LLM service not enabled")
    try:
        yield
    except HTTPException:
        raise
    except ImportError:
        logger.error("litellm package not installed")
        raise HTTPException(status_code=500, detail="LLM service not configured") from None
    except Exception as e:
        logger.error(f"LLM call error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM service error: {e!s}") from e


def complete(messages: list, model: str | None = None) -> dict:
    """Create a completion. Returns dict with content/model/usage."""
    with _llm_available():
        import litellm

        response = litellm.completion(**_build_completion_kwargs(messages, model))
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": dict(response.usage) if response.usage else None,
        }


def complete_stream(messages: list, model: str | None = None) -> Generator[str]:
    """Streaming variant of :func:`complete`. Yields content chunks."""
    with _llm_available():
        import litellm

        response = litellm.completion(**_build_completion_kwargs(messages, model, stream=True))
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
