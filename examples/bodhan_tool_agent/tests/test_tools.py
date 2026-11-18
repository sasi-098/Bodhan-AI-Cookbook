"""Unit tests for the 5 MCP tools."""

import tempfile
import time
from pathlib import Path

from bodhan_mcp.tools.inspect_tool import run_inspect_media
from bodhan_mcp.tools.media_utils import create_synthetic_wav
from bodhan_mcp.tools.ocr import run_ocr
from bodhan_mcp.tools.speak import run_speak
from bodhan_mcp.tools.transcribe import run_transcribe
from bodhan_mcp.tools.translate import run_translate


def test_transcribe_tool():
    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = Path(tmp_dir) / "sample.wav"
        create_synthetic_wav(wav_path, duration_sec=5.0)

        res = run_transcribe(str(wav_path), language="hi")
        assert res["success"] is True
        assert len(res["text"]) > 0
        assert res["duration_seconds"] == 5.0
        assert res["chunks_count"] == 1
        assert res["nominal_cost_inr"] > 0


def test_transcribe_missing_file():
    res = run_transcribe("non_existent_file.wav")
    assert res["success"] is False
    assert "not found" in res["error"].lower()


def test_translate_tool_supported():
    res = run_translate("Water boils at 100 degrees.", target_lang="hi")
    assert res["success"] is True
    assert len(res["translation"]) > 0
    assert res["target_lang"] == "hi"


def test_translate_tool_unsupported_language():
    # French is unsupported by Bodhan Indic models
    res = run_translate("Translate this video into French", target_lang="fr")
    assert res["success"] is False
    assert "unsupported target language" in res["error"].lower()
    assert res["translation"] == ""


def test_translate_indic_to_indic_pivot():
    # Hindi to Tamil (should trigger pivot)
    res = run_translate("यह एक परीक्षण है।", target_lang="ta", source_lang="hi")
    assert res["success"] is True
    assert res["pivoted_via_english"] is True
    assert len(res["translation"]) > 0


def test_speak_tool():
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_wav = Path(tmp_dir) / "test_out.wav"
        unique_text = f"नमस्ते, आप कैसे हैं? {time.time()}"
        res = run_speak(unique_text, language="hi", output_path=str(out_wav))
        assert res["success"] is True
        assert Path(res["audio_file"]).is_file()
        assert res["language"] == "hi"
        assert res["duration_seconds"] > 0
        assert res["cost_inr"] > 0
        assert res["nominal_cost_inr"] > 0


def test_ocr_tool():
    with tempfile.TemporaryDirectory() as tmp_dir:
        img_path = Path(tmp_dir) / "test_page.png"
        from PIL import Image
        img = Image.new("RGB", (800, 600), "white")
        img.save(img_path)

        res = run_ocr(str(img_path))
        assert res["success"] is True
        assert len(res["markdown"]) > 0
        assert res["page_count"] == 1
        assert res["nominal_cost_inr"] == 0.20


def test_inspect_media():
    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = Path(tmp_dir) / "test.wav"
        create_synthetic_wav(wav_path, duration_sec=4.0)
        res = run_inspect_media(str(wav_path))
        assert res["success"] is True
        assert res["file_type"] == "audio"
        assert res["duration_seconds"] == 4.0
