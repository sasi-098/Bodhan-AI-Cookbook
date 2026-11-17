"""Unit tests for artifact verification (audio back-transcription, table integrity)."""

import tempfile
from pathlib import Path

from bodhan_agent.verifier import ArtifactVerifier
from bodhan_mcp.tools.media_utils import create_synthetic_wav


def test_verify_valid_audio():
    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = Path(tmp_dir) / "test_speech.wav"
        create_synthetic_wav(wav_path, duration_sec=3.0)

        verifier = ArtifactVerifier()
        res = verifier.verify_artifacts([wav_path], target_lang="hi")

        assert res["verified_count"] == 1
        assert res["all_passed"] is True
        assert res["checks"][0]["passed"] is True
        assert res["checks"][0]["type"] == "audio"
        assert res["checks"][0]["back_transcription_success"] is True


def test_verify_missing_file():
    verifier = ArtifactVerifier()
    res = verifier.verify_artifacts([Path("non_existent_file.wav")])

    assert res["verified_count"] == 1
    assert res["all_passed"] is False
    assert res["checks"][0]["passed"] is False
    assert res["checks"][0]["type"] == "missing"


def test_verify_empty_text_file():
    with tempfile.TemporaryDirectory() as tmp_dir:
        txt_path = Path(tmp_dir) / "empty.txt"
        txt_path.write_text("   \n", encoding="utf-8")

        verifier = ArtifactVerifier()
        res = verifier.verify_artifacts([txt_path])

        assert res["verified_count"] == 1
        assert res["all_passed"] is False
        assert res["checks"][0]["passed"] is False


def test_verify_table_markdown():
    with tempfile.TemporaryDirectory() as tmp_dir:
        table_path = Path(tmp_dir) / "worksheet_table.md"
        table_path.write_text(
            "# Math Table\n\n| Item | Value |\n| --- | --- |\n| Area | 50 |\n",
            encoding="utf-8"
        )

        verifier = ArtifactVerifier()
        res = verifier.verify_artifacts([table_path])

        assert res["verified_count"] == 1
        assert res["all_passed"] is True
        assert res["checks"][0]["has_table_structure"] is True
