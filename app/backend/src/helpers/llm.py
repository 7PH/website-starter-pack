# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
LLM integration helper using LiteLLM.
Provides unified interface for LLM completions across multiple providers.
"""

import logging
import os
from collections.abc import Generator

from fastapi import HTTPException

from ..constants import LLM_API_BASE, LLM_API_KEY, LLM_ENABLED, LLM_MODEL, LLM_PROVIDER

logger = logging.getLogger(__name__)


def init_llm() -> None:
    """Initialize LLM with API keys. Call this at app startup."""
    if not LLM_ENABLED:
        logger.info("LLM integration disabled")
        return

    # LiteLLM uses environment variables for API keys
    # Set the appropriate key based on provider
    if LLM_API_KEY:
        if LLM_PROVIDER == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = LLM_API_KEY
        elif LLM_PROVIDER == "openai":
            os.environ["OPENAI_API_KEY"] = LLM_API_KEY
        elif LLM_PROVIDER == "azure":
            os.environ["AZURE_API_KEY"] = LLM_API_KEY
        # For other providers, set the generic key
        # LiteLLM will pick it up based on the model prefix

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


def complete(
    messages: list,
    model: str | None = None,
) -> dict:
    """
    Create a completion using LiteLLM.

    Args:
        messages: List of message dicts or LLMMessage objects
        model: Optional model override

    Returns:
        Dict with 'content', 'model', and 'usage' keys

    Raises:
        HTTPException if LLM is not enabled or on API errors
    """
    if not LLM_ENABLED:
        raise HTTPException(status_code=503, detail="LLM service not enabled")

    try:
        import litellm

        model_name = get_model_name(model)
        converted_messages = _convert_messages(messages)

        # Build kwargs for the completion call
        kwargs: dict = {
            "model": model_name,
            "messages": converted_messages,
        }

        # Add API base for providers that need it
        if LLM_API_BASE and LLM_PROVIDER in ("ollama", "azure"):
            kwargs["api_base"] = LLM_API_BASE

        response = litellm.completion(**kwargs)

        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": dict(response.usage) if response.usage else None,
        }

    except ImportError:
        logger.error("litellm package not installed")
        raise HTTPException(status_code=500, detail="LLM service not configured") from None
    except Exception as e:
        logger.error(f"LLM completion error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM service error: {e!s}") from e


def complete_stream(
    messages: list,
    model: str | None = None,
) -> Generator[str]:
    """
    Create a streaming completion using LiteLLM.

    Args:
        messages: List of message dicts or LLMMessage objects
        model: Optional model override

    Yields:
        Content chunks as strings

    Raises:
        HTTPException if LLM is not enabled or on API errors
    """
    if not LLM_ENABLED:
        raise HTTPException(status_code=503, detail="LLM service not enabled")

    try:
        import litellm

        model_name = get_model_name(model)
        converted_messages = _convert_messages(messages)

        # Build kwargs for the completion call
        kwargs: dict = {
            "model": model_name,
            "messages": converted_messages,
            "stream": True,
        }

        # Add API base for providers that need it
        if LLM_API_BASE and LLM_PROVIDER in ("ollama", "azure"):
            kwargs["api_base"] = LLM_API_BASE

        response = litellm.completion(**kwargs)

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except ImportError:
        logger.error("litellm package not installed")
        raise HTTPException(status_code=500, detail="LLM service not configured") from None
    except Exception as e:
        logger.error(f"LLM streaming error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM service error: {e!s}") from e
