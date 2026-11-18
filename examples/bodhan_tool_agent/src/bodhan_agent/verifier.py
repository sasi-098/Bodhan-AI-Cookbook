"""Robust verification suite for generated artifacts with semantic fidelity and number preservation."""

from __future__ import annotations

import difflib
import re
import time
from pathlib import Path
from typing import Any

from bodhan_mcp.cost import CostTracker
from bodhan_mcp.tools.media_utils import detect_script_and_language, inspect_audio_file
from bodhan_mcp.tools.transcribe import run_transcribe


def compute_text_similarity(str1: str, str2: str) -> float:
    """Compute normalized sequence similarity ratio between two strings (0.0 to 1.0)."""
    norm1 = re.sub(r"[^\w\s]", "", str1.lower().strip())
    norm2 = re.sub(r"[^\w\s]", "", str2.lower().strip())
    if not norm1 and not norm2:
        return 1.0
    return difflib.SequenceMatcher(None, norm1, norm2).ratio()


def extract_numbers(text: str) -> list[str]:
    """Extract numeric sequences from text."""
    return re.findall(r"\d+", text)


class ArtifactVerifier:
    """Performs strict pre-completion verification and gating on all generated artifacts."""

    def verify_artifacts(
        self,
        artifact_paths: list[Path],
        target_lang: str = "auto",
        expected_text: str = "",
        cost_tracker: CostTracker | None = None,
    ) -> dict[str, Any]:
        """Verify each generated artifact: audio back-transcription, semantic fidelity, and number preservation."""
        results: list[dict[str, Any]] = []
        all_passed = True

        for path in artifact_paths:
            p = Path(path)
            if not p.is_file():
                results.append({
                    "artifact": str(p),
                    "type": "missing",
                    "passed": False,
                    "error": "Artifact file does not exist on disk.",
                })
                all_passed = False
                continue

            suffix = p.suffix.lower()

            # 1. Verify Audio Artifacts via Back-Transcription & Fidelity Check
            if suffix in (".wav", ".mp3", ".ogg", ".m4a"):
                audio_info = inspect_audio_file(p)
                duration = audio_info.get("duration_seconds", 0.0)

                if duration <= 0.0 or audio_info.get("is_corrupted"):
                    results.append({
                        "artifact": p.name,
                        "type": "audio",
                        "passed": False,
                        "back_transcription_success": False,
                        "error": audio_info.get("error", "Audio duration is 0 seconds."),
                    })
                    all_passed = False
                    continue

                # Run back-transcription with Indic-Transcribe
                asr_res = run_transcribe(str(p), language=target_lang if target_lang != "auto" else None)
                back_transcript = asr_res.get("text", "")

                # Record back-transcription cost into cost tracker if provided
                if cost_tracker and asr_res.get("cost_inr", 0) > 0:
                    cost_tracker.record_cost(
                        model="indic-transcribe",
                        operation="verification_back_transcription",
                        metric="inr",
                        quantity=asr_res["cost_inr"],
                        cost_inr=asr_res["cost_inr"],
                        timestamp=time.time(),
                    )

                audio_passed = asr_res.get("success", False) and len(back_transcript.strip()) > 0
                error_reasons: list[str] = []

                if not audio_passed:
                    error_reasons.append("Back-transcription failed or produced empty text.")

                # If expected_text is supplied, verify number preservation & semantic similarity
                similarity = 1.0
                if expected_text and back_transcript:
                    expected_nums = extract_numbers(expected_text)
                    actual_nums = extract_numbers(back_transcript)
                    
                    # Number preservation check
                    missing_nums = [n for n in expected_nums if n not in actual_nums]
                    if missing_nums:
                        audio_passed = False
                        error_reasons.append(f"Number preservation failure: numbers {missing_nums} missing from speech.")

                    similarity = round(compute_text_similarity(expected_text, back_transcript), 3)
                    # For realistic speech back-transcription, require reasonable similarity
                    if similarity < 0.35 and len(expected_text) > 20:
                        audio_passed = False
                        error_reasons.append(f"Semantic fidelity too low: similarity score {similarity} < 0.35.")

                if not audio_passed:
                    all_passed = False

                results.append({
                    "artifact": p.name,
                    "type": "audio",
                    "duration_seconds": duration,
                    "back_transcript": back_transcript[:120] + ("..." if len(back_transcript) > 120 else ""),
                    "similarity_score": similarity,
                    "passed": audio_passed,
                    "back_transcription_success": bool(asr_res.get("success", False)),
                    "errors": error_reasons if not audio_passed else [],
                })

            # 2. Verify Text / Markdown / Subtitle Artifacts
            elif suffix in (".md", ".txt", ".srt", ".vtt", ".json"):
                try:
                    content = p.read_text(encoding="utf-8")
                    char_count = len(content.strip())

                    script_info = detect_script_and_language(content)
                    has_table = "|" in content if ("table" in p.name.lower() or suffix == ".md") else True

                    text_passed = char_count > 0 and has_table
                    error_reasons = []

                    if char_count == 0:
                        text_passed = False
                        error_reasons.append("Empty text file.")
                    if not has_table and "table" in p.name.lower():
                        text_passed = False
                        error_reasons.append("Expected Markdown table structure '|' missing.")

                    # Number preservation check if expected_text provided
                    if expected_text and content:
                        expected_nums = extract_numbers(expected_text)
                        actual_nums = extract_numbers(content)
                        missing_nums = [n for n in expected_nums if n not in actual_nums]
                        if missing_nums:
                            text_passed = False
                            error_reasons.append(f"Numbers missing in translation: {missing_nums}")

                    if not text_passed:
                        all_passed = False

                    results.append({
                        "artifact": p.name,
                        "type": "text",
                        "char_count": char_count,
                        "detected_script": script_info.get("script", "Unknown"),
                        "inferred_language": script_info.get("inferred_language", "unknown"),
                        "has_table_structure": has_table,
                        "passed": text_passed,
                        "errors": error_reasons if not text_passed else [],
                    })
                except Exception as e:
                    results.append({
                        "artifact": p.name,
                        "type": "text",
                        "passed": False,
                        "error": str(e),
                    })
                    all_passed = False

            # Other files
            else:
                passed = p.stat().st_size > 0
                if not passed:
                    all_passed = False
                results.append({
                    "artifact": p.name,
                    "type": "binary",
                    "size_bytes": p.stat().st_size,
                    "passed": passed,
                })

        return {
            "verified_count": len(results),
            "all_passed": all_passed if results else True,
            "checks": results,
        }


artifact_verifier = ArtifactVerifier()
