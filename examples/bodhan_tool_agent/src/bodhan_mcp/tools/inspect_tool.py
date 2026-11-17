"""Helper inspection tool for media analysis and language/script identification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bodhan_mcp.tools.media_utils import (
    detect_script_and_language,
    inspect_audio_file,
    inspect_image_file,
    inspect_pdf_file,
)


def run_inspect_media(file_path: str) -> dict[str, Any]:
    """Inspect input files (audio, image, PDF, or text) to detect format, size, duration, pages, or language script.
    
    Helper tool to assist the agent in planning before invoking paid model tools.
    """
    p = Path(file_path).resolve()
    if not p.is_file():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "file_type": "unknown",
        }

    suffix = p.suffix.lower()

    try:
        # Audio
        if suffix in (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"):
            info = inspect_audio_file(p)
            return {
                "success": True,
                "file_type": "audio",
                "format": info.get("format", suffix.lstrip(".")),
                "duration_seconds": info.get("duration_seconds", 0.0),
                "channels": info.get("channels", 1),
                "sample_rate": info.get("framerate", 16000),
                "size_bytes": p.stat().st_size,
            }

        # PDF
        elif suffix == ".pdf":
            info = inspect_pdf_file(p)
            return {
                "success": True,
                "file_type": "pdf",
                "page_count": info.get("page_count", 0),
                "size_bytes": p.stat().st_size,
            }

        # Images
        elif suffix in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
            info = inspect_image_file(p)
            return {
                "success": True,
                "file_type": "image",
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "format": info.get("format", suffix.lstrip(".").upper()),
                "size_bytes": p.stat().st_size,
            }

        # Text files / transcripts / subtitles
        elif suffix in (".txt", ".md", ".json", ".srt", ".vtt", ".csv"):
            content = p.read_text(encoding="utf-8", errors="replace")
            script_info = detect_script_and_language(content)
            return {
                "success": True,
                "file_type": "text",
                "char_count": len(content),
                "detected_script": script_info.get("script", "Unknown"),
                "inferred_language": script_info.get("inferred_language", "unknown"),
                "confidence": script_info.get("confidence", 0.0),
                "size_bytes": p.stat().st_size,
            }

        else:
            return {
                "success": True,
                "file_type": "binary",
                "extension": suffix,
                "size_bytes": p.stat().st_size,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to inspect media file: {str(e)}",
            "file_type": "error",
        }
