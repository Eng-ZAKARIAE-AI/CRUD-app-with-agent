"""Pydantic schemas for the multimodal agent API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Current user message")
    images: list[str] = Field(
        default_factory=list,
        description="Optional image URLs or base64 data URLs (JPEG/PNG)",
    )
    history: list[ChatHistoryItem] = Field(
        default_factory=list,
        description="Prior conversation turns (text only)",
    )


class AgentChatResponse(BaseModel):
    reply: str
