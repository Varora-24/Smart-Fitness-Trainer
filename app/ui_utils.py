"""
app/ui_utils.py — Shared Streamlit UI Helper Functions
======================================================
Contains robust rendering utilities for Streamlit pages, separated from backend config.
"""

from __future__ import annotations
import os
from pathlib import Path
import streamlit as st


def display_reference_image(cfg: dict, title_prefix: str = "") -> None:
    """Safely render target exercise or pose reference images across different operating systems and working directories."""
    if "image_url" not in cfg:
        return

    raw_path = cfg["image_url"]
    display_name = cfg.get("display_name", cfg.get("name", ""))
    source_text = cfg.get("image_source", "SmartTrainer AI Vector Reference")
    caption = f"{title_prefix}{display_name} — {source_text}".strip()

    # Determine project root cleanly via __file__ (repository root is parent of app/)
    repo_root = Path(__file__).resolve().parent.parent
    candidate_path = repo_root / raw_path

    if candidate_path.exists():
        st.image(str(candidate_path), use_container_width=True, caption=caption)
    elif os.path.exists(raw_path):
        st.image(raw_path, use_container_width=True, caption=caption)
    else:
        # Fallback for HTTP URLs or unverified paths
        try:
            st.image(raw_path, use_container_width=True, caption=caption)
        except Exception:
            st.error(f"Image reference unavailable: {raw_path}")
