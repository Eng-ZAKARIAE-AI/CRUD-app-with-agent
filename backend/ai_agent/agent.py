"""Multimodal AI agent powered by OpenRouter."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI
load_dotenv = os.getenv("LOAD_DOTENV", "true").lower() == "true"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = (
    "You are a helpful multimodal inventory assistant for a product CRUD app. "
    "You can read text and images (product photos, labels, invoices, screenshots). "
    "Be concise, practical, and accurate. If an image is provided, ground your "
    "answer in what you actually see. When unsure, say so."
)


def _require_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Export your OpenRouter API key, e.g. "
            "`export OPENROUTER_API_KEY=...` (get one at https://openrouter.ai)."
        )
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)


def _build_user_content(message: str, images: list[str]) -> list[dict[str, Any]] | str:
    """Build Responses API content: optional images + text."""
    text = (message or "").strip()
    clean_images = [img for img in images if img and img.strip()]

    if not clean_images:
        return text or "Hello"

    content: list[dict[str, Any]] = []
    for image_url in clean_images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_url},
            }
        )
    content.append(
        {
            "type": "text",
            "text": text or "Please describe what you see in the image(s).",
        }
    )
    return content


def run_multimodal_chat(
    message: str,
    *,
    images: list[str] | None = None,
    history: list[dict[str, str]] | None = None,
    model: str | None = None,
) -> str:
    """
    Run one multimodal chat turn against OpenRouter.

    Args:
        message: Current user text prompt.
        images: Optional list of image URLs or data URLs (JPEG/PNG).
        history: Prior turns as ``{"role": "user"|"assistant", "content": "..."}``.
        model: Override model id (default ``grok-4.5``).

    Returns:
        Assistant reply text.
    """
    client = _require_client()
    images = images or []
    history = history or []

    input_items: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    for turn in history:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        input_items.append({"role": role, "content": content})

    input_items.append(
        {
            "role": "user",
            "content": _build_user_content(message, images),
        }
    )

    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=input_items,
    )

    text = response.choices[0].message.content
    if text:
        return str(text).strip()

    return str(response)
