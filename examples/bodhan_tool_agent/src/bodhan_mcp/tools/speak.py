"""Indic-Speak MCP tool with sentence chunking, WAV concatenation, and cost tracking."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any

from bodhan_mcp.cache import cache
from bodhan_mcp.client import bodhan_client
from bodhan_mcp.cost import calculate_speak_cost
from bodhan_mcp.tools.media_utils import (
    concatenate_wav_files,
    inspect_audio_file,
    split_text_into_sentences,
)


def run_speak(
    text: str,
    language: str,
    voice: str | None = None,
    style: str = "educational lecture",
    output_path: str | None = None,
) -> dict[str, Any]:
    """Synthesize speech audio from text using Bodhan Indic-Speak.
    
    Splits long inputs into natural sentence chunks, synthesizes each,
    and stitches them into a seamless PCM16 WAV audio file.
    
    Returns file reference to the audio, never base64.
    """
    start_time = time.time()
    if not text or not text.strip():
        return {
            "success": False,
            "error": "Input text cannot be empty.",
            "audio_file": "",
            "cost_inr": 0.0,
        }

    norm_lang = language.strip().lower()

    # Determine destination audio path
    if output_path:
        final_output = Path(output_path).resolve()
        final_output.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = Path("outputs/audio").resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        final_output = out_dir / f"speech_{norm_lang}_{int(time.time()*1000)}.wav"

    try:
        # Split into short sentence chunks to stay under model limits
        chunks = split_text_into_sentences(text, max_chunk_chars=220)
        temp_audio_files: list[Path] = []
        total_cost = 0.0

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                cache_key = cache.compute_key(
                    "indic-speak",
                    chunk,
                    language=norm_lang,
                    voice=voice,
                    style=style,
                )
                cached_res = cache.get(cache_key)

                chunk_audio_file = tmp_path / f"part_{idx:03d}.wav"

                if cached_res and Path(cached_res["audio_file"]).is_file():
                    # Copy cached audio
                    chunk_audio_file.write_bytes(Path(cached_res["audio_file"]).read_bytes())
                else:
                    bodhan_client.synthesize_speech_chunk(
                        text=chunk,
                        language=norm_lang,
                        voice=voice,
                        style=style,
                        output_file=chunk_audio_file,
                    )
                    chunk_cost = calculate_speak_cost(len(chunk))
                    total_cost += chunk_cost
                    cache.set(
                        cache_key,
                        {
                            "audio_file": str(chunk_audio_file),
                            "chars_count": len(chunk),
                            "cost_inr": chunk_cost,
                        },
                    )

                temp_audio_files.append(chunk_audio_file)

            if not temp_audio_files:
                return {
                    "success": False,
                    "error": "No audio chunks could be synthesized.",
                    "audio_file": "",
                    "cost_inr": 0.0,
                }

            # Concatenate chunks into final WAV
            concatenate_wav_files(temp_audio_files, final_output)

        audio_info = inspect_audio_file(final_output)
        latency_sec = round(time.time() - start_time, 2)

        return {
            "success": True,
            "audio_file": str(final_output),
            "language": norm_lang,
            "voice": voice or "default",
            "style": style,
            "duration_seconds": audio_info.get("duration_seconds", 0.0),
            "sample_rate": audio_info.get("framerate", 24000),
            "characters_count": len(text),
            "chunks_count": len(chunks),
            "cost_inr": round(total_cost, 4),
            "latency_seconds": latency_sec,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Speech synthesis failed: {str(e)}",
            "audio_file": "",
            "cost_inr": 0.0,
        }
