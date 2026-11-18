"""Pytest configuration ensuring unit tests run deterministically in mock mode."""

import os

# Force mock mode for unit tests to prevent outbound network calls and paid API usage
os.environ["BODHAN_MOCK"] = "1"
