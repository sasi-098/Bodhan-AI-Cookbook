"""HTTP client for Bodhan Indic APIs with retries, backoff, and mock fallback."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import requests

from bodhan_mcp.config import (
    BASE_URL,
    MOCK_MODE,
    OCR_KEY,
    SPEAK_KEY,
    TRANSCRIBE_KEY,
    TRANSLATE_KEY,
)
from bodhan_mcp.tools.media_utils import create_synthetic_wav


class BodhanClient:
    """Client for Bodhan's Indic AI APIs with robust error handling and mock support."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0):
        self.base_url = (base_url or BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _headers(self, api_key: str, content_type: Optional[str] = None) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {api_key}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _execute_with_retry(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str],
        max_retries: int = 3,
        **kwargs: Any,
    ) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        last_exception = None

        for attempt in range(max_retries):
            try:
                resp = self.session.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
                if resp.status_code == 429:
                    # Rate limit or quota hit - backoff
                    retry_after = float(resp.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(retry_after)
                    continue
                if resp.status_code >= 500:
                    time.sleep(1.5 ** attempt)
                    continue
                if not resp.ok:
                    try:
                        err = resp.json().get("error", {})
                        raise RuntimeError(
                            f"Bodhan API Error {resp.status_code} [{err.get('code', 'unknown')}]: "
                            f"{err.get('message', resp.text)}"
                        )
                    except (ValueError, KeyError):
                        resp.raise_for_status()
                return resp
            except (requests.ConnectionError, requests.Timeout) as e:
                last_exception = e
                time.sleep(1.5 ** attempt)

        raise RuntimeError(f"Bodhan API call failed after {max_retries} attempts: {last_exception}")

    # ------------------------------------------------------------------------
    # Indic-Transcribe
    # ------------------------------------------------------------------------
    def transcribe_audio_chunk(
        self,
        audio_file: str | Path,
        language: Optional[str] = None,
    ) -> str:
        """Transcribe an audio chunk (<= 30s) using Indic-Transcribe."""
        p = Path(audio_file)
        if not p.is_file():
            raise FileNotFoundError(f"Audio file not found: {p}")

        if MOCK_MODE:
            # Simulated realistic transcription
            lang_label = language or "hi"
            simulated_text = {
                "hi": "नमस्ते, यह बोधन एआई प्रतिलेखन का एक उदाहरण है।",
                "ta": "வணக்கம், இது போதன் ஏஐ டிரான்ஸ்கிரிப்ஷனின் மாதிரி ஆகும்.",
                "bn": "নমস্কার, এটি বোধন এআই প্রতিলিপির একটি উদাহরণ।",
                "te": "నమస్కారం, ఇది బోధన్ ఏఐ ట్రాన్స్క్రిప్షన్ యొక్క నమూనా.",
                "en": "Hello, this is a sample transcription produced by Bodhan AI.",
            }
            return simulated_text.get(lang_label, simulated_text["en"])

        headers = self._headers(TRANSCRIBE_KEY)
        data = {"model": "indic-transcribe"}
        if language:
            data["language"] = language

        with open(p, "rb") as fh:
            resp = self._execute_with_retry(
                "POST",
                "/v1/audio/transcriptions",
                headers=headers,
                files={"file": (p.name, fh, "audio/wav")},
                data=data,
            )
        return resp.json().get("text", "")

    # ------------------------------------------------------------------------
    # Indic-Translate
    # ------------------------------------------------------------------------
    def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
    ) -> str:
        """Translate text into target language using Indic-Translate."""
        if not text.strip():
            return ""

        if MOCK_MODE:
            # Deterministic translation mapping for mock testing
            translations = {
                "hi": f"अनुवाद [हिंदी]: {text}",
                "ta": f"மொழிபெயர்ப்பு [தமிழ்]: {text}",
                "bn": f"অনুবাদ [বাংলা]: {text}",
                "te": f"అనువాదం [తెలుగు]: {text}",
                "mr": f"भाषांतर [मराठी]: {text}",
                "en": f"English translation: {text}",
            }
            return translations.get(target_lang, f"[{target_lang}] {text}")

        headers = self._headers(TRANSLATE_KEY, content_type="application/json")
        body: Dict[str, Any] = {
            "text": text,
            "target_language": target_lang,
        }
        if source_lang:
            body["source_language"] = source_lang

        resp = self._execute_with_retry("POST", "/translate", headers=headers, json=body)
        return resp.json().get("translation", "")

    # ------------------------------------------------------------------------
    # Indic-Speak
    # ------------------------------------------------------------------------
    def synthesize_speech_chunk(
        self,
        text: str,
        language: str,
        voice: Optional[str] = None,
        style: str = "educational lecture",
        output_file: Optional[str | Path] = None,
    ) -> Path:
        """Synthesize a short sentence/chunk into PCM16 WAV audio using Indic-Speak."""
        out_p = Path(output_file) if output_file else Path(f"speech_{int(time.time()*1000)}.wav")
        out_p.parent.mkdir(parents=True, exist_ok=True)

        # Default voices per language if not specified
        default_voices = {
            "hi": "Kavya",
            "ta": "Anitha",
            "bn": "Ishita",
            "te": "Sravani",
            "mr": "Anagha",
            "en": "Amit",
        }
        selected_voice = voice or default_voices.get(language, "Amit")

        if MOCK_MODE:
            # Create a synthetic WAV file proportional to text length
            duration = max(1.0, min(25.0, len(text) * 0.05))
            return create_synthetic_wav(out_p, duration_sec=duration, sample_rate=24000)

        headers = self._headers(SPEAK_KEY, content_type="application/json")
        body = {
            "model": "indic-speak",
            "input": text,
            "voice": selected_voice,
            "instructions": json.dumps({"lang": language, "style": style}),
        }

        resp = self._execute_with_retry("POST", "/v1/audio/speech", headers=headers, json=body)
        out_p.write_bytes(resp.content)
        return out_p

    # ------------------------------------------------------------------------
    # Indic-OCR
    # ------------------------------------------------------------------------
    def ocr_image(
        self,
        image_path: str | Path,
        table_format: str = "markdown",
    ) -> Dict[str, Any]:
        """Extract text, tables, and layout blocks from an image page using Indic-OCR."""
        p = Path(image_path)
        if not p.is_file():
            raise FileNotFoundError(f"Image file not found: {p}")

        if MOCK_MODE:
            # Realistic OCR mock response
            return {
                "markdown": f"# Document Section\n\nExtracted content from {p.name}.\n\n| Item | Value |\n| --- | --- |\n| Example | 100% |\n",
                "blocks": [
                    {
                        "order": 1,
                        "label": "title",
                        "conf": 0.98,
                        "bbox_xyxy": [50, 40, 800, 100],
                        "text": "Document Section",
                    },
                    {
                        "order": 2,
                        "label": "paragraph",
                        "conf": 0.95,
                        "bbox_xyxy": [50, 120, 800, 200],
                        "text": f"Extracted content from {p.name}.",
                    },
                ],
            }

        mime_type = mimetypes.guess_type(str(p))[0] or "image/png"
        b64_img = base64.b64encode(p.read_bytes()).decode("utf-8")

        headers = self._headers(OCR_KEY, content_type="application/json")
        body = {
            "model": "indic-ocr",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_img}"},
                        }
                    ],
                }
            ],
            "table_format": table_format,
        }

        resp = self._execute_with_retry("POST", "/v1/chat/completions", headers=headers, json=body)
        data = resp.json()

        markdown_text = ""
        if "choices" in data and len(data["choices"]) > 0:
            markdown_text = data["choices"][0].get("message", {}).get("content", "")

        blocks = data.get("blocks", [])
        return {"markdown": markdown_text, "blocks": blocks}


# Global client instance
bodhan_client = BodhanClient()
