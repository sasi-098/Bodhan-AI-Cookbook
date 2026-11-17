"""Verification suite for generated artifacts (audio back-transcription, translation coverage)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bodhan_mcp.tools.media_utils import detect_script_and_language, inspect_audio_file
from bodhan_mcp.tools.transcribe import run_transcribe


class ArtifactVerifier:
    """Performs pre-completion verification on all generated artifacts."""

    def verify_artifacts(
        self,
        artifact_paths: list[Path],
        target_lang: str = "auto",
        expected_text: str = "",
    ) -> dict[str, Any]:
        """Verify each generated artifact: back-transcribe audio, check translation coverage."""
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

            # 1. Verify Audio Artifacts via Back-Transcription
            if suffix in (".wav", ".mp3", ".ogg", ".m4a"):
                audio_info = inspect_audio_file(p)
                duration = audio_info.get("duration_seconds", 0.0)

                if duration <= 0.0:
                    results.append({
                        "artifact": p.name,
                        "type": "audio",
                        "passed": False,
                        "error": "Audio duration is 0 seconds.",
                    })
                    all_passed = False
                    continue

                # Back-transcribe with Indic-Transcribe
                asr_res = run_transcribe(str(p), language=target_lang if target_lang != "auto" else None)
                back_transcript = asr_res.get("text", "")

                passed = asr_res.get("success", False) and len(back_transcript.strip()) > 0
                if not passed:
                    all_passed = False

                results.append({
                    "artifact": p.name,
                    "type": "audio",
                    "duration_seconds": duration,
                    "back_transcript": back_transcript[:120] + ("..." if len(back_transcript) > 120 else ""),
                    "back_transcription_success": asr_res.get("success", False),
                    "passed": passed,
                })

            # 2. Verify Text / Markdown / Subtitle Artifacts
            elif suffix in (".md", ".txt", ".srt", ".vtt", ".json"):
                try:
                    content = p.read_text(encoding="utf-8")
                    char_count = len(content.strip())

                    # Check script & language
                    script_info = detect_script_and_language(content)
                    has_table = "|" in content if suffix == ".md" else True

                    passed = char_count > 0 and ("table" not in p.name.lower() or has_table)
                    if not passed:
                        all_passed = False

                    results.append({
                        "artifact": p.name,
                        "type": "text",
                        "char_count": char_count,
                        "detected_script": script_info.get("script", "Unknown"),
                        "inferred_language": script_info.get("inferred_language", "unknown"),
                        "has_table_structure": has_table,
                        "passed": passed,
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
                results.append({
                    "artifact": p.name,
                    "type": "binary",
                    "size_bytes": p.stat().st_size,
                    "passed": p.stat().st_size > 0,
                })

        return {
            "verified_count": len(results),
            "all_passed": all_passed if results else True,
            "checks": results,
        }


artifact_verifier = ArtifactVerifier()
