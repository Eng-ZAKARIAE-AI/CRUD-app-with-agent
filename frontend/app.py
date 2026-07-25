"""Streamlit multipage app — top navbar with Inventory and AI Agent routes."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

PAGES_DIR = Path(__file__).resolve().parent / "pages"

st.set_page_config(
    page_title="CRUD + AI Agent",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

inventory_page = st.Page(
    str(PAGES_DIR / "inventory.py"),
    title="Inventory",
    icon="📦",
    default=True,
)
ai_agent_page = st.Page(
    str(PAGES_DIR / "ai_agent.py"),
    title="AI Agent",
    icon="🤖",
)

nav = st.navigation(
    [inventory_page, ai_agent_page],
    position="top",
)
nav.run()
