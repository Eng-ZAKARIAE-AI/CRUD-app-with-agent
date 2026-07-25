"""Shared HTTP helpers for talking to the Product CRUD + Agent API."""

from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
PRODUCTS_URL = f"{API_BASE_URL}/products/"
AGENT_CHAT_URL = f"{API_BASE_URL}/agent/chat"


def _error_detail(response: requests.Response) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail", response.text)
        if isinstance(detail, list):
            return "; ".join(
                item.get("msg", str(item)) if isinstance(item, dict) else str(item)
                for item in detail
            )
        return str(detail)
    except Exception:
        return response.text or f"HTTP {response.status_code}"


def fetch_products(active_only: bool = False) -> list[dict[str, Any]]:
    response = requests.get(
        PRODUCTS_URL,
        params={"skip": 0, "limit": 500, "active_only": active_only},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def create_product(payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        PRODUCTS_URL,
        json=payload,
        timeout=10,
    )
    if response.status_code >= 400:
        raise requests.HTTPError(_error_detail(response), response=response)
    return response.json()


def update_product(product_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.patch(
        f"{API_BASE_URL}/products/{product_id}",
        json=payload,
        timeout=10,
    )
    if response.status_code >= 400:
        raise requests.HTTPError(_error_detail(response), response=response)
    return response.json()


def delete_product(product_id: int, soft: bool = True) -> None:
    response = requests.delete(
        f"{API_BASE_URL}/products/{product_id}",
        params={"soft": str(soft).lower()},
        timeout=10,
    )
    if response.status_code >= 400:
        raise requests.HTTPError(_error_detail(response), response=response)


def chat_with_agent(
    message: str,
    *,
    images: list[str] | None = None,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Send a multimodal chat turn to the backend agent. Returns assistant text."""
    response = requests.post(
        AGENT_CHAT_URL,
        json={
            "message": message,
            "images": images or [],
            "history": history or [],
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise requests.HTTPError(_error_detail(response), response=response)
    payload = response.json()
    return str(payload.get("reply", ""))
