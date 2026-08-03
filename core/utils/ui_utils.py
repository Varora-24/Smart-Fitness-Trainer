"""
core/utils/ui_utils.py — Shared Streamlit UI Helper Functions
=============================================================
Contains robust rendering utilities for Streamlit pages within the recognized core package.
"""

from __future__ import annotations
import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components


def render_tts_bridge(phrase: str, ts: float, key_prefix: str = "tts") -> None:
    """
    Robust Web Speech API Bridge for Streamlit Community Cloud & Local deployment.
    Avoids cross-origin SecurityErrors by executing speech synthesis directly within
    the local iframe scope while logging explicit diagnostics to the browser F12 console.
    """
    if not phrase:
        return

    session_key = f"{key_prefix}_last_spoken_ts"
    if session_key not in st.session_state:
        st.session_state[session_key] = 0.0

    # Only speak if we have a newer timestamp than previously voiced in this session
    if ts <= st.session_state[session_key]:
        return

    st.session_state[session_key] = ts

    # Sanitize phrase for JavaScript insertion
    safe_phrase = phrase.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    components.html(
        f"""
        <script>
        (function() {{
            console.log("[SmartTrainer TTS] New voice cue queued: '{safe_phrase}' (ts: {ts})");
            try {{
                // Always check local window scope first to prevent cross-origin SecurityErrors
                var win = ('speechSynthesis' in window) ? window : (window.parent && 'speechSynthesis' in window.parent ? window.parent : null);
                if (!win) {{
                    console.error("[SmartTrainer TTS] Web Speech API not available in browser.");
                    return;
                }}

                win.speechSynthesis.cancel();
                var u = new win.SpeechSynthesisUtterance("{safe_phrase}");
                u.rate = 1.05;
                u.volume = 1.0;
                u.onstart = function() {{ console.log("[SmartTrainer TTS] Speaking audio: '{safe_phrase}'"); }};
                u.onerror = function(err) {{ console.error("[SmartTrainer TTS] Audio playback error:", err.error, err); }};
                win.speechSynthesis.speak(u);
            }} catch (e) {{
                console.error("[SmartTrainer TTS] Fatal speech synthesis exception:", e);
            }}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


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
