"""
tests/conftest.py

Ensures the repository root is on sys.path so test modules can import
top-level application modules (exercises, voice_coach, session_tracker,
exercise_classifier, etc.) directly, e.g. `from exercises import ExerciseTracker`.

This is a deliberate belt-and-suspenders fallback alongside the
`[tool.pytest.ini_options] pythonpath = ["."]` setting in pyproject.toml.
Both do the same job; keeping both means the test suite still collects
correctly even if a given pytest/CI environment ignores one of them.
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
