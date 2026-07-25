"""Multimodal AI agent powered by OpenRouter."""

from __future__ import annotations

import os
from typing import Any

import json
from sqlalchemy.orm import Session
from backend.crud_app.services.product_service import ProductService
from backend.crud_app.repositories.product_repository import ProductRepository
from backend.crud_app.schemas.product_schema import ProductCreate, ProductUpdate


from openai import OpenAI
load_dotenv = os.getenv("LOAD_DOTENV", "true").lower() == "true"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_products",
            "description": "List products in the database. Can limit results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of products to return"},
                    "skip": {"type": "integer", "description": "Number of products to skip"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "Get a single product by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"}
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_product",
            "description": "Create a new product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "sku": {"type": "string"},
                    "price": {"type": "number"},
                    "stock_quantity": {"type": "integer"}
                },
                "required": ["name", "sku", "price"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_product",
            "description": "Update an existing product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "sku": {"type": "string"},
                    "price": {"type": "number"},
                    "stock_quantity": {"type": "integer"}
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_product",
            "description": "Delete a product by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"}
                },
                "required": ["product_id"]
            }
        }
    }
]

def execute_tool(tool_call, db: Session):
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    repo = ProductRepository(db)
    service = ProductService(repo, db)
    
    try:
        if func_name == "list_products":
            limit = args.get("limit", 100)
            skip = args.get("skip", 0)
            products = service.list_products(skip=skip, limit=limit)
            return json.dumps([p.__dict__ for p in products], default=str)
        elif func_name == "get_product":
            product = service.get_product(args["product_id"])
            return json.dumps(product.__dict__, default=str)
        elif func_name == "create_product":
            dto = ProductCreate(**args)
            product = service.create_product(dto)
            return json.dumps(product.__dict__, default=str)
        elif func_name == "update_product":
            product_id = args.pop("product_id")
            dto = ProductUpdate(**args)
            product = service.update_product(product_id, dto)
            return json.dumps(product.__dict__, default=str)
        elif func_name == "delete_product":
            service.delete_product(args["product_id"])
            return json.dumps({"status": "success", "message": f"Product {args['product_id']} deleted"})
        else:
            return json.dumps({"error": "Unknown function"})
    except Exception as e:
        return json.dumps({"error": str(e)})

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
    db: Session | None = None,
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

    for _ in range(5):  # Max 5 tool call loops
        response = client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=input_items,
            tools=TOOLS if db else None,
        )

        message = response.choices[0].message
        
        if message.tool_calls and db:
            input_items.append(message)
            for tool_call in message.tool_calls:
                result = execute_tool(tool_call, db)
                input_items.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            if message.content:
                return str(message.content).strip()
            return str(response)
            
    return "Error: Exceeded maximum tool call iterations." 
