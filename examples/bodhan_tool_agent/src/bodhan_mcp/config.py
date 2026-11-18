"""Configuration and environment variables for Bodhan MCP Server."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Automatically load .env if present from cwd, recipe directory, or repo root
load_dotenv()
_recipe_env = Path(__file__).resolve().parents[2] / ".env"
if _recipe_env.is_file():
    load_dotenv(_recipe_env)
_repo_env = Path(__file__).resolve().parents[4] / ".env"
if _repo_env.is_file():
    load_dotenv(_repo_env)

BASE_URL = os.environ.get("BODHAN_BASE_URL", "https://api.bodhan.ai").rstrip("/")

# Primary API Key
BODHAN_API_KEY = os.environ.get("BODHAN_API_KEY", "")

# Model-specific API keys (fallback to BODHAN_API_KEY)
TRANSCRIBE_KEY = os.environ.get("BODHAN_TRANSCRIBE_KEY") or BODHAN_API_KEY
TRANSLATE_KEY = os.environ.get("BODHAN_TRANSLATE_KEY") or BODHAN_API_KEY
SPEAK_KEY = os.environ.get("BODHAN_SPEAK_KEY") or BODHAN_API_KEY
OCR_KEY = os.environ.get("BODHAN_OCR_KEY") or BODHAN_API_KEY

# LLM Configuration for Agent
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

# Mock Mode (active if BODHAN_MOCK=1 or when keys are placeholders/empty)
_mock_env = os.environ.get("BODHAN_MOCK", "").lower() in ("1", "true", "yes")
_keys_missing = not (TRANSCRIBE_KEY or TRANSLATE_KEY or SPEAK_KEY or OCR_KEY)
_is_placeholder = any(
    "placeholder" in k.lower() or "your_" in k.lower()
    for k in [TRANSCRIBE_KEY, TRANSLATE_KEY, SPEAK_KEY, OCR_KEY]
    if k
)
MOCK_MODE = _mock_env or _keys_missing or _is_placeholder

# Cache directory for audio, documents, and API responses
CACHE_DIR = Path(os.environ.get("BODHAN_CACHE_DIR", ".bodhan_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
