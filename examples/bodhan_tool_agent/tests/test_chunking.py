"""Unit tests for media chunking, stitching, and script detection."""

import tempfile
from pathlib import Path

from bodhan_mcp.tools.media_utils import (
    chunk_wav_audio,
    concatenate_wav_files,
    create_synthetic_wav,
    detect_script_and_language,
    inspect_audio_file,
    split_text_into_sentences,
)


def test_synthetic_wav_and_inspect():
    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = Path(tmp_dir) / "test.wav"
        create_synthetic_wav(wav_path, duration_sec=3.0, sample_rate=24000)
        assert wav_path.is_file()

        info = inspect_audio_file(wav_path)
        assert info["format"] == "wav"
        assert info["channels"] == 1
        assert info["framerate"] == 24000
        assert info["duration_seconds"] == 3.0


def test_chunk_and_concatenate_audio():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        wav_path = tmp_path / "long_audio.wav"
        # Create 60 second audio
        create_synthetic_wav(wav_path, duration_sec=60.0, sample_rate=16000)

        chunks = chunk_wav_audio(wav_path, chunk_duration_sec=25.0, output_dir=tmp_path / "chunks")
        # 60 seconds with 25s chunks -> 3 chunks (25s, 25s, 10s)
        assert len(chunks) == 3

        # Re-concatenate
        merged_path = tmp_path / "merged.wav"
        concatenate_wav_files(chunks, merged_path)
        assert merged_path.is_file()

        info = inspect_audio_file(merged_path)
        assert abs(info["duration_seconds"] - 60.0) < 0.1


def test_sentence_splitting():
    text = (
        "नमस्ते दोस्तों! यह एक परीक्षण वाक्य है। क्या आप मुझे सुन सकते हैं? "
        "हाँ, बोधन एआई बहुत अच्छी सेवा प्रदान करता है।"
    )
    chunks = split_text_into_sentences(text, max_chunk_chars=50)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 60


def test_script_detection():
    # Hindi / Devanagari
    res_hi = detect_script_and_language("यह हिंदी का एक वाक्य है।")
    assert res_hi["script"] == "Devanagari"
    assert res_hi["inferred_language"] == "hi"

    # Tamil
    res_ta = detect_script_and_language("இது ஒரு தமிழ் வாக்கியம்.")
    assert res_ta["script"] == "Tamil"
    assert res_ta["inferred_language"] == "ta"

    # Bengali
    res_bn = detect_script_and_language("এটি একটি বাংলা বাক্য।")
    assert res_bn["script"] == "Bengali"
    assert res_bn["inferred_language"] == "bn"

    # English
    res_en = detect_script_and_language("This is a plain English sentence.")
    assert res_en["script"] == "Latin"
    assert res_en["inferred_language"] == "en"
