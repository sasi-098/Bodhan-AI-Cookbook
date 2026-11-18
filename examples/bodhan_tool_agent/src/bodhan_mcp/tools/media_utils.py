"""Media utility functions for audio, image, PDF handling, and script detection."""

from __future__ import annotations

import math
import re
import shutil
import struct
import wave
from pathlib import Path
from typing import Any

from PIL import Image
from pypdf import PdfReader


def inspect_audio_file(path: str | Path) -> dict[str, Any]:
    """Inspect WAV audio file properties (duration, sample rate, channels)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    # Inspect WAV using standard wave module
    try:
        with wave.open(str(p), "rb") as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            frames = wf.getnframes()
            duration_sec = frames / float(framerate) if framerate > 0 else 0.0
            return {
                "format": "wav",
                "channels": channels,
                "sample_width": sample_width,
                "framerate": framerate,
                "frames": frames,
                "duration_seconds": round(duration_sec, 2),
                "size_bytes": p.stat().st_size,
            }
    except wave.Error:
        size = p.stat().st_size
        # If it has a .wav suffix or size < 44 bytes (minimum WAV header), it's corrupted/invalid WAV
        if p.suffix.lower() == ".wav" or size < 44:
            return {
                "format": p.suffix.lstrip(".").lower(),
                "channels": 0,
                "sample_width": 0,
                "framerate": 0,
                "frames": 0,
                "duration_seconds": 0.0,
                "size_bytes": size,
                "is_corrupted": True,
                "error": "Corrupted or invalid WAV file header",
            }
        # Fallback approximation for compressed audio formats (mp3, ogg, m4a)
        est_duration = round(size / 32000.0, 2)
        return {
            "format": p.suffix.lstrip(".").lower(),
            "channels": 1,
            "framerate": 16000,
            "duration_seconds": est_duration,
            "size_bytes": size,
            "note": "Estimated metrics (non-standard WAV or compressed format)",
        }


def chunk_wav_audio(
    path: str | Path,
    chunk_duration_sec: float = 25.0,
    output_dir: Path | None = None,
) -> list[Path]:
    """Split a WAV audio file into chunks of duration <= chunk_duration_sec."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    target_dir = output_dir or p.parent / f"{p.stem}_chunks"
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        with wave.open(str(p), "rb") as wf:
            params = wf.getparams()
            framerate = wf.getframerate()
            total_frames = wf.getnframes()
            duration = total_frames / float(framerate)

            if duration <= chunk_duration_sec:
                return [p]

            frames_per_chunk = int(framerate * chunk_duration_sec)
            chunks: list[Path] = []
            chunk_idx = 0

            while True:
                chunk_frames = wf.readframes(frames_per_chunk)
                if not chunk_frames:
                    break
                chunk_path = target_dir / f"{p.stem}_part{chunk_idx:03d}.wav"
                with wave.open(str(chunk_path), "wb") as out_wf:
                    out_wf.setparams(params)
                    out_wf.writeframes(chunk_frames)
                chunks.append(chunk_path)
                chunk_idx += 1

            return chunks
    except Exception:
        # If wave module fails on non-WAV, return single file
        return [p]


def concatenate_wav_files(input_paths: list[Path], output_path: str | Path) -> Path:
    """Concatenate multiple WAV files into a single WAV file."""
    if not input_paths:
        raise ValueError("No input files provided for concatenation.")

    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if len(input_paths) == 1:
        shutil.copyfile(str(input_paths[0]), str(out_p))
        return out_p

    with wave.open(str(input_paths[0]), "rb") as first_wf:
        params = first_wf.getparams()

    with wave.open(str(out_p), "wb") as out_wf:
        out_wf.setparams(params)
        for p in input_paths:
            with wave.open(str(p), "rb") as in_wf:
                out_wf.writeframes(in_wf.readframes(in_wf.getnframes()))

    return out_p


def create_synthetic_wav(
    output_path: str | Path,
    duration_sec: float = 2.0,
    sample_rate: int = 24000,
    frequency: float = 440.0,
) -> Path:
    """Generate a valid PCM16 mono WAV file (useful for tests and synthetic audio)."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(duration_sec * sample_rate)
    amplitude = 16000

    with wave.open(str(p), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            val = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return p


def inspect_image_file(path: str | Path) -> dict[str, Any]:
    """Inspect image dimensions and format."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")

    with Image.open(p) as img:
        width, height = img.size
        img_format = img.format or p.suffix.lstrip(".").upper()
        return {
            "format": img_format,
            "width": width,
            "height": height,
            "mode": img.mode,
            "size_bytes": p.stat().st_size,
        }


def inspect_pdf_file(path: str | Path) -> dict[str, Any]:
    """Inspect PDF page count and metadata."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    reader = PdfReader(str(p))
    page_count = len(reader.pages)
    return {
        "format": "pdf",
        "page_count": page_count,
        "size_bytes": p.stat().st_size,
    }


def split_pdf_to_images(
    pdf_path: str | Path,
    output_dir: Path | None = None,
) -> list[Path]:
    """Convert each PDF page to an image.
    Uses pypdf embedded image extraction or generates rendered page placeholders.
    """
    p = Path(pdf_path)
    target_dir = output_dir or p.parent / f"{p.stem}_pages"
    target_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(p))
    image_paths: list[Path] = []

    for idx, page in enumerate(reader.pages):
        page_img_path = target_dir / f"page_{idx + 1:03d}.png"
        
        # Check if page has embedded images
        extracted = False
        if page.images:
            for img_file in page.images:
                with open(page_img_path, "wb") as fp:
                    fp.write(img_file.data)
                extracted = True
                break

        if not extracted:
            # Fallback: render text as image using Pillow
            img = Image.new("RGB", (1200, 1600), "white")
            page_text = page.extract_text() or ""
            if page_text:
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                y = 40
                for line in page_text.splitlines()[:50]:
                    if line.strip():
                        draw.text((40, y), line.strip()[:100], fill="black")
                        y += 30
            img.save(page_img_path, "PNG")

        image_paths.append(page_img_path)

    return image_paths


def detect_script_and_language(text: str) -> dict[str, Any]:
    """Detect Indic script and infer language based on Unicode character counts."""
    counts = {
        "Devanagari": len(re.findall(r"[\u0900-\u097F]", text)),
        "Bengali": len(re.findall(r"[\u0980-\u09FF]", text)),
        "Gurmukhi": len(re.findall(r"[\u0A00-\u0A7F]", text)),
        "Gujarati": len(re.findall(r"[\u0A80-\u0AFF]", text)),
        "Odia": len(re.findall(r"[\u0B00-\u0B7F]", text)),
        "Tamil": len(re.findall(r"[\u0B80-\u0BFF]", text)),
        "Telugu": len(re.findall(r"[\u0C00-\u0C7F]", text)),
        "Kannada": len(re.findall(r"[\u0C80-\u0CFF]", text)),
        "Malayalam": len(re.findall(r"[\u0D00-\u0D7F]", text)),
        "Perso-Arabic": len(re.findall(r"[\u0600-\u06FF]", text)),
        "Latin": len(re.findall(r"[A-Za-z]", text)),
    }

    dominant_script, max_count = max(counts.items(), key=lambda item: item[1])
    if max_count == 0:
        return {"script": "Unknown", "inferred_language": "unknown", "confidence": 0.0}

    # Map script to probable language
    script_to_lang = {
        "Devanagari": "hi",  # Hindi / Marathi / Sanskrit
        "Bengali": "bn",     # Bengali / Assamese
        "Gurmukhi": "pa",    # Punjabi
        "Gujarati": "gu",    # Gujarati
        "Odia": "or",        # Odia
        "Tamil": "ta",       # Tamil
        "Telugu": "te",      # Telugu
        "Kannada": "kn",     # Kannada
        "Malayalam": "ml",   # Malayalam
        "Perso-Arabic": "ur",# Urdu / Sindhi
        "Latin": "en",       # English
    }

    total_chars = max(1, sum(counts.values()))
    confidence = round(max_count / total_chars, 2)
    return {
        "script": dominant_script,
        "inferred_language": script_to_lang.get(dominant_script, "unknown"),
        "confidence": confidence,
        "counts": counts,
    }


def split_text_into_sentences(text: str, max_chunk_chars: int = 250) -> list[str]:
    """Split text into sentences respecting Indic punctuation (danda ।, etc.) and length."""
    # Split by standard punctuation and Indic danda
    raw_sentences = re.split(r"(?<=[.!?।\n])\s+", text.strip())
    chunks: list[str] = []
    current_chunk = ""

    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        if len(current_chunk) + len(s) + 1 <= max_chunk_chars:
            current_chunk = f"{current_chunk} {s}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If single sentence exceeds max_chunk_chars, split by commas or words
            if len(s) > max_chunk_chars:
                sub_parts = re.split(r"(?<=[,;])\s+", s)
                sub_chunk = ""
                for part in sub_parts:
                    if len(sub_chunk) + len(part) + 1 <= max_chunk_chars:
                        sub_chunk = f"{sub_chunk} {part}".strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = part
                if sub_chunk:
                    chunks.append(sub_chunk)
                current_chunk = ""
            else:
                current_chunk = s

    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [text]
