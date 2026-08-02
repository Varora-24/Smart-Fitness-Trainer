"""
core/utils/ui_utils.py — Shared Streamlit UI Helper Functions
=============================================================
Contains robust rendering utilities for Streamlit pages within the recognized core package.
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

    # Determine project root cleanly via __file__ (repository root is 3 levels above core/utils/ui_utils.py)
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidate_paths = [
        Path(raw_path),
        repo_root / raw_path,
        Path.cwd() / raw_path,
    ]

    img_file = None
    for cp in candidate_paths:
        if cp.exists():
            img_file = cp
            break

    if img_file is not None:
        st.image(str(img_file), use_container_width=True, caption=caption)
    elif os.path.exists(raw_path):
        st.image(raw_path, use_container_width=True, caption=caption)
    else:
        # Fallback for HTTP URLs or unverified paths
        try:
            st.image(raw_path, use_container_width=True, caption=caption)
        except Exception:
            st.error(f"Image reference unavailable: {raw_path}")
