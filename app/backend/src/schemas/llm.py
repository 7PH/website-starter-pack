# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""LLM-related Pydantic schemas for API requests/responses."""

from typing import Literal

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """A single message in a conversation."""

    role: Literal["system", "user", "assistant"]
    content: str


class LLMCompletionRequest(BaseModel):
    """Request schema for creating a completion."""

    messages: list[LLMMessage]
    model: str | None = None  # Override default model
    stream: bool = False


class LLMCompletionResponse(BaseModel):
    """Response schema for a completion."""

    content: str
    model: str
    usage: dict | None = None  # Token counts if available


class LLMStatusResponse(BaseModel):
    """Response schema for LLM service status."""

    enabled: bool
    provider: str | None = None
    model: str | None = None
