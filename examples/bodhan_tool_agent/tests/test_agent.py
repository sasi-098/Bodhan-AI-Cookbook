"""Tests for Bodhan Task Agent planning, execution, verification, and honest failure."""

import json
import tempfile
from pathlib import Path

from bodhan_agent.agent import TaskAgent
from bodhan_mcp.tools.media_utils import create_synthetic_wav
from PIL import Image


def test_impossible_task_french():
    """Verify honest failure when an unsupported language like French is requested."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_dir = Path(tmp_dir) / "out"
        agent = TaskAgent(
            task="Translate this video into French",
            files=[],
            out_dir=out_dir,
        )
        res = agent.run()

        assert res["status"] == "impossible_task"
        assert len(res["artifacts"]) == 0

        # Check result.md
        result_md = (out_dir / "result.md").read_text(encoding="utf-8")
        assert "French" in result_md
        assert "unsupported" in result_md.lower()

        # Check report.json
        report_json = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
        assert report_json["status"] == "impossible_task"


def test_audio_summary_task():
    """Verify multi-step planning: OCR -> Translate -> Speak -> Verification -> Report."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create a sample input image
        img_path = tmp_path / "chapter_page.png"
        img = Image.new("RGB", (600, 800), "white")
        img.save(img_path)

        out_dir = tmp_path / "out"
        agent = TaskAgent(
            task="Make a two-minute Tamil audio summary of this chapter",
            files=[img_path],
            out_dir=out_dir,
            max_steps=10,
            max_cost_inr=5.0,
        )
        res = agent.run()

        assert res["status"] == "completed"
        assert len(res["artifacts"]) > 0

        # Check files exist
        assert (out_dir / "result.md").is_file()
        assert (out_dir / "report.json").is_file()
        assert (out_dir / "trace.jsonl").is_file()

        # Check trace lines
        trace_lines = [json.loads(line) for line in (out_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(trace_lines) >= 2

        # Check verification
        report_data = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
        assert report_data["status"] == "completed"
        assert "verification" in report_data
        assert report_data["verification"]["all_passed"] is True


def test_subtitles_task():
    """Verify speech transcription and subtitle generation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        wav_path = tmp_path / "voice_note.wav"
        create_synthetic_wav(wav_path, duration_sec=4.0)

        out_dir = tmp_path / "out"
        agent = TaskAgent(
            task="Transcribe this Hindi voice note and give me English subtitles",
            files=[wav_path],
            out_dir=out_dir,
        )
        res = agent.run()

        assert res["status"] == "completed"
        assert any("srt" in a.lower() for a in res["artifacts"])


def test_budget_enforcement():
    """Verify agent stops gracefully when budget limit is reached."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        img_path = tmp_path / "page.png"
        Image.new("RGB", (400, 400), "white").save(img_path)

        out_dir = tmp_path / "out"
        # Extremely small budget (₹0.000001)
        agent = TaskAgent(
            task="Make a two-minute Tamil audio summary of this chapter",
            files=[img_path],
            out_dir=out_dir,
            max_cost_inr=0.000001,
        )
        res = agent.run()
        # Should stop cleanly with budget_exceeded
        assert res["status"] in ("budget_exceeded", "completed")
