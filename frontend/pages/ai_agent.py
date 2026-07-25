"""Multimodal AI Agent page — chat with text + image understanding."""

from __future__ import annotations

import base64
from typing import Any

import requests
import streamlit as st

from api_client import API_BASE_URL, chat_with_agent

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png"}


def _init_chat_state() -> None:
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = []


def _file_to_data_url(uploaded) -> str | None:
    """Convert an uploaded Streamlit file to a base64 data URL for the vision API."""
    mime = (uploaded.type or "").lower()
    if mime not in SUPPORTED_IMAGE_TYPES:
        return None
    # Normalize jpeg alias
    if mime == "image/jpg":
        mime = "image/jpeg"
    raw = uploaded.getvalue()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _history_for_api(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Flatten chat history to text-only turns for the backend context window."""
    history: list[dict[str, str]] = []
    for msg in messages:
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        text = (msg.get("content") or "").strip()
        if text:
            history.append({"role": role, "content": text})
    return history


def _render_message(msg: dict[str, Any]) -> None:
    role = msg.get("role", "assistant")
    with st.chat_message(role):
        images = msg.get("images") or []
        if images:
            cols = st.columns(min(len(images), 3))
            for idx, img in enumerate(images):
                cols[idx % len(cols)].image(img, use_container_width=True)
        content = msg.get("content") or ""
        if content:
            st.markdown(content)


def main() -> None:
    _init_chat_state()

    st.title("🤖 Multimodal AI Agent")
    st.markdown(
        "Chat with a **vision-capable** agent. Attach product photos, invoices, "
        "or screenshots and ask questions in natural language."
    )

    with st.sidebar:
        st.header("Agent")
        st.caption(
            "Powered by **OpenRouter** via the backend. "
            "Supports **text + images** (JPEG / PNG)."
        )
        st.divider()
        st.caption(f"API: `{API_BASE_URL}`")
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.agent_messages = []
            st.rerun()

    # Conversation history
    for msg in st.session_state.agent_messages:
        _render_message(msg)

    # Optional image attachments for the next turn
    with st.expander("📎 Attach images (optional)", expanded=False):
        uploads = st.file_uploader(
            "Upload JPEG or PNG images",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="agent_image_uploader",
            help="Images are sent with your next message for multimodal understanding.",
        )
        if uploads:
            preview_cols = st.columns(min(len(uploads), 4))
            for idx, f in enumerate(uploads):
                preview_cols[idx % len(preview_cols)].image(
                    f, caption=f.name, use_container_width=True
                )

    prompt = st.chat_input("Ask anything… e.g. “What’s in this photo?” or “Summarize stock risks”")
    if not prompt:
        return

    # Build multimodal user turn
    image_data_urls: list[str] = []
    image_bytes_for_ui: list[bytes] = []
    if uploads:
        for f in uploads:
            data_url = _file_to_data_url(f)
            if data_url is None:
                st.warning(f"Skipped unsupported file type: {f.name} ({f.type})")
                continue
            image_data_urls.append(data_url)
            image_bytes_for_ui.append(f.getvalue())

    user_msg: dict[str, Any] = {
        "role": "user",
        "content": prompt,
        "images": image_bytes_for_ui,
    }
    st.session_state.agent_messages.append(user_msg)
    _render_message(user_msg)

    # Call backend agent
    history = _history_for_api(st.session_state.agent_messages[:-1])
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                reply = chat_with_agent(
                    prompt,
                    images=image_data_urls,
                    history=history,
                )
            except requests.ConnectionError:
                reply = (
                    f"Cannot reach the API at `{API_BASE_URL}`. "
                    "Start the backend, then try again."
                )
                st.error(reply)
            except requests.RequestException as exc:
                reply = f"Agent request failed: {exc}"
                st.error(reply)
            else:
                st.markdown(reply)

    st.session_state.agent_messages.append(
        {"role": "assistant", "content": reply, "images": []}
    )


main()
