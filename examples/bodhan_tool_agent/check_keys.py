"""Quick connectivity and authentication checker for Bodhan API keys."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from bodhan_mcp.config import (
    BASE_URL,
    MOCK_MODE,
    OCR_KEY,
    SPEAK_KEY,
    TRANSCRIBE_KEY,
    TRANSLATE_KEY,
)
from bodhan_mcp.tools.media_utils import create_synthetic_wav
from bodhan_mcp.tools.ocr import run_ocr
from bodhan_mcp.tools.speak import run_speak
from bodhan_mcp.tools.transcribe import run_transcribe
from bodhan_mcp.tools.translate import run_translate
from PIL import Image


def main() -> int:
    print("=" * 65)
    print("        BODHAN AI API KEYS CONNECTIVITY & AUTH CHECK")
    print("=" * 65)
    print(f"Base URL: {BASE_URL}")
    print(f"Mock Mode: {'ACTIVE (Simulated)' if MOCK_MODE else 'OFF (Live calls to api.bodhan.ai)'}")
    print("-" * 65)

    def mask(k: str) -> str:
        if not k:
            return "<UNSET>"
        if len(k) <= 8:
            return k[:2] + "****"
        return k[:4] + "****" + k[-4:]

    print(f"1. Indic-Translate Key  : {mask(TRANSLATE_KEY)}")
    print(f"2. Indic-Speak Key      : {mask(SPEAK_KEY)}")
    print(f"3. Indic-Transcribe Key : {mask(TRANSCRIBE_KEY)}")
    print(f"4. Indic-OCR Key        : {mask(OCR_KEY)}")
    print("-" * 65)

    if MOCK_MODE:
        print("NOTE: Real keys not detected or BODHAN_MOCK=1 is set.")
        print("Please set your keys in .env to test live connectivity.")
        print("=" * 65)
        return 0

    all_passed = True

    # 1. Test Translate
    print("\n▶ Testing Indic-Translate...")
    try:
        res = run_translate("Hello, welcome to Bodhan AI.", target_lang="hi")
        if res.get("success"):
            print(f"  [PASS] Translation: {res.get('translation', '')[:60]}")
        else:
            print(f"  [FAIL] Error: {res.get('error')}")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        all_passed = False

    # 2. Test Speak
    print("\n▶ Testing Indic-Speak...")
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_wav = Path(tmp_dir) / "test_speak.wav"
            res = run_speak("नमस्ते बोधन", language="hi", output_path=str(out_wav))
            if res.get("success") and Path(res.get("audio_file", "")).is_file():
                print(f"  [PASS] Speech synthesized ({res.get('duration_seconds')}s WAV generated)")
            else:
                print(f"  [FAIL] Error: {res.get('error')}")
                all_passed = False
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        all_passed = False

    # 3. Test Transcribe
    print("\n▶ Testing Indic-Transcribe...")
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = Path(tmp_dir) / "test_asr.wav"
            create_synthetic_wav(wav_path, duration_sec=2.0)
            res = run_transcribe(str(wav_path), language="hi")
            if res.get("success"):
                print(f"  [PASS] Transcription response: '{res.get('text', '')[:60]}'")
            else:
                print(f"  [FAIL] Error: {res.get('error')}")
                all_passed = False
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        all_passed = False

    # 4. Test OCR
    print("\n▶ Testing Indic-OCR...")
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            img_path = Path(tmp_dir) / "test_ocr.png"
            img = Image.new("RGB", (300, 100), "white")
            img.save(img_path)
            res = run_ocr(str(img_path))
            if res.get("success"):
                print("  [PASS] OCR processed successfully")
            else:
                print(f"  [FAIL] Error: {res.get('error')}")
                all_passed = False
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print("RESULT: ALL 4 BODHAN AI KEYS AUTHENTICATED & OPERATIONAL!")
    else:
        print("RESULT: Some keys failed authentication. Check the errors above.")
    print("=" * 65)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
