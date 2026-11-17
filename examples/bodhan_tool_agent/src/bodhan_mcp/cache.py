"""Deduplication cache for Bodhan model API calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bodhan_mcp.config import CACHE_DIR


class ResponseCache:
    """Thread-safe persistent cache to prevent redundant paid model calls."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, Any] = {}

    @staticmethod
    def compute_file_hash(path: str | Path) -> str:
        """Compute SHA256 of a file."""
        p = Path(path)
        if not p.is_file():
            return hashlib.sha256(str(path).encode("utf-8")).hexdigest()
        hasher = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def compute_key(tool: str, payload_data: Any, **kwargs: Any) -> str:
        """Create a deterministic cache key from tool name, payload, and kwargs."""
        hasher = hashlib.sha256()
        hasher.update(tool.encode("utf-8"))

        if isinstance(payload_data, (str, Path)) and Path(payload_data).is_file():
            hasher.update(ResponseCache.compute_file_hash(payload_data).encode("utf-8"))
        elif isinstance(payload_data, str):
            hasher.update(payload_data.encode("utf-8"))
        elif isinstance(payload_data, (dict, list)):
            hasher.update(json.dumps(payload_data, sort_keys=True).encode("utf-8"))
        elif payload_data is not None:
            hasher.update(str(payload_data).encode("utf-8"))

        if kwargs:
            hasher.update(json.dumps(kwargs, sort_keys=True, default=str).encode("utf-8"))

        return hasher.hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve cached result by key if present."""
        if key in self._memory_cache:
            return self._memory_cache[key]

        disk_path = self.cache_dir / f"{key}.json"
        if disk_path.is_file():
            try:
                data = json.loads(disk_path.read_text(encoding="utf-8"))
                self._memory_cache[key] = data
                return data
            except Exception:
                return None
        return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Store result in cache."""
        self._memory_cache[key] = value
        disk_path = self.cache_dir / f"{key}.json"
        try:
            disk_path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


# Global cache instance
cache = ResponseCache()
