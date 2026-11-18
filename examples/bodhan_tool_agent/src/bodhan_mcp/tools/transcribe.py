"""Indic-Transcribe MCP tool with automatic audio chunking and cost tracking."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from bodhan_mcp.cache import cache
from bodhan_mcp.client import bodhan_client
from bodhan_mcp.cost import calculate_transcribe_cost
from bodhan_mcp.tools.media_utils import chunk_wav_audio, inspect_audio_file


def run_transcribe(
    audio_path: str,
    language: str | None = None,
) -> dict[str, Any]:
    """Transcribe speech in an audio file using Indic-Transcribe.
    
    Handles audio files of any length by automatically splitting files longer than
    30 seconds into chunks, transcribing each, and joining the results.
    """
    start_time = time.time()
    if language:
        from bodhan_mcp.tools.translate import LANGUAGE_ALIASES
        language = LANGUAGE_ALIASES.get(language.strip().lower(), language)
    p = Path(audio_path)
    if not p.is_file():
        return {
            "success": False,
            "error_code": "FILE_NOT_FOUND",
            "error": f"Audio file not found: {audio_path}",
            "text": "",
            "cost_inr": 0.0,
            "duration_seconds": 0.0,
        }

    try:
        audio_info = inspect_audio_file(p)
        total_duration = audio_info.get("duration_seconds", 0.0)
        if audio_info.get("is_corrupted") or total_duration <= 0.0:
            return {
                "success": False,
                "error_code": "CORRUPTED_MEDIA",
                "error": "Corrupted audio file or duration is 0 seconds.",
                "text": "",
                "cost_inr": 0.0,
                "duration_seconds": 0.0,
            }

        # Automatic chunking if audio > 28 seconds
        chunks = chunk_wav_audio(p, chunk_duration_sec=25.0) if total_duration > 28.0 else [p]

        transcripts = []
        total_cost = 0.0
        cache_hits = 0

        for chunk in chunks:
            chunk_info = inspect_audio_file(chunk)
            chunk_duration = chunk_info.get("duration_seconds", 0.0)

            # Check cache
            cache_key = cache.compute_key("indic-transcribe", chunk, language=language)
            cached_res = cache.get(cache_key)

            if cached_res:
                transcripts.append(cached_res["text"])
                cache_hits += 1
            else:
                chunk_text = bodhan_client.transcribe_audio_chunk(chunk, language=language)
                chunk_cost = calculate_transcribe_cost(chunk_duration)
                total_cost += chunk_cost
                cache.set(cache_key, {"text": chunk_text, "duration": chunk_duration, "cost_inr": chunk_cost})
                transcripts.append(chunk_text)

        full_transcript = " ".join(t.strip() for t in transcripts if t.strip())
        latency_sec = round(time.time() - start_time, 2)
        nominal_cost = calculate_transcribe_cost(total_duration)

        return {
            "success": True,
            "text": full_transcript,
            "language": language or "auto",
            "duration_seconds": total_duration,
            "chunks_count": len(chunks),
            "cost_inr": round(total_cost, 4),
            "nominal_cost_inr": round(nominal_cost, 4),
            "is_cached": cache_hits == len(chunks),
            "latency_seconds": latency_sec,
        }

    except Exception as e:
        return {
            "success": False,
            "error_code": "TRANSCRIPTION_FAILED",
            "error": f"Transcription failed: {str(e)}",
            "text": "",
            "cost_inr": 0.0,
            "duration_seconds": 0.0,
        }
