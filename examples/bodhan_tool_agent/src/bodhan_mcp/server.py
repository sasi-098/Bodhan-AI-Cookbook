"""Bodhan MCP Tool Server definition using standard Model Context Protocol."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from bodhan_mcp.tools.inspect_tool import run_inspect_media
from bodhan_mcp.tools.ocr import run_ocr
from bodhan_mcp.tools.speak import run_speak
from bodhan_mcp.tools.transcribe import run_transcribe
from bodhan_mcp.tools.translate import run_translate

# Initialize MCPServer
mcp_server = MCPServer(
    name="bodhan_mcp",
    title="Bodhan AI Indic Tools Server",
    description="MCP Server exposing Bodhan's Indic Speech-to-Text, Translation, TTS, and OCR models as tools.",
    version="0.1.0",
)


# ----------------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------------

@mcp_server.tool(
    name="bodhan_transcribe",
    description=(
        "Transcribe speech from an audio file using Bodhan Indic-Transcribe. "
        "Supports 25 Indic languages and English. Automatically splits audio longer than 30s "
        "into chunks and returns concatenated transcript with timestamps and cost."
    ),
)
def transcribe_tool(audio_path: str, language: str | None = None) -> str:
    """Transcribe speech in an audio file.
    
    Args:
        audio_path: Path to the local audio file (e.g. WAV or MP3).
        language: Optional ISO language code (e.g. 'hi', 'ta', 'bn', 'en'). Auto-detected if omitted.
    """
    res = run_transcribe(audio_path=audio_path, language=language)
    return json.dumps(res, ensure_ascii=False)


@mcp_server.tool(
    name="bodhan_translate",
    description=(
        "Translate text into an Indian language or English using Bodhan Indic-Translate. "
        "Supports 25 Indic languages and English. Automatically handles Indic-to-Indic "
        "translations via English pivot when required."
    ),
)
def translate_tool(text: str, target_lang: str, source_lang: str | None = None) -> str:
    """Translate text into a target language.
    
    Args:
        text: The source text to translate.
        target_lang: Target ISO language code (e.g. 'hi', 'ta', 'bn', 'mr', 'te', 'en').
        source_lang: Optional source ISO language code. Auto-detected if omitted.
    """
    res = run_translate(text=text, target_lang=target_lang, source_lang=source_lang)
    return json.dumps(res, ensure_ascii=False)


@mcp_server.tool(
    name="bodhan_speak",
    description=(
        "Synthesize natural speech in an Indian language or English using Bodhan Indic-Speak. "
        "Splits long text into sentence chunks to preserve natural pacing and stitches "
        "them into a single PCM16 WAV audio file. Returns path to the audio file."
    ),
)
def speak_tool(
    text: str,
    language: str,
    voice: str | None = None,
    style: str = "educational lecture",
    output_path: str | None = None,
) -> str:
    """Synthesize speech audio from text.
    
    Args:
        text: Text to speak (must be in target language or English).
        language: Target ISO language code (e.g. 'hi', 'ta', 'bn').
        voice: Optional voice name from Bodhan voice library (e.g. 'Kavya', 'Anitha', 'Amit').
        style: Speaking style (e.g. 'educational lecture', 'AIR style news', 'Customer Care').
        output_path: Optional destination file path for generated WAV file.
    """
    res = run_speak(text=text, language=language, voice=voice, style=style, output_path=output_path)
    return json.dumps(res, ensure_ascii=False)


@mcp_server.tool(
    name="bodhan_ocr",
    description=(
        "Extract text, tables, equations (LaTeX), and layout from an image or multi-page PDF "
        "using Bodhan Indic-OCR. Returns Markdown text and structured layout blocks."
    ),
)
def ocr_tool(file_path: str, table_format: str = "markdown") -> str:
    """Perform document OCR on an image or PDF.
    
    Args:
        file_path: Path to the local image (PNG/JPG) or PDF document.
        table_format: Format for tables: 'markdown' or 'html'.
    """
    res = run_ocr(file_path=file_path, table_format=table_format)
    return json.dumps(res, ensure_ascii=False)


@mcp_server.tool(
    name="inspect_media",
    description=(
        "Inspect an input media file (audio duration, sample rate, image dimensions, "
        "PDF page count, or text language and script detection) without invoking paid model APIs."
    ),
)
def inspect_tool(file_path: str) -> str:
    """Inspect media file properties.
    
    Args:
        file_path: Path to the media or text file to analyze.
    """
    res = run_inspect_media(file_path=file_path)
    return json.dumps(res, ensure_ascii=False)


# ----------------------------------------------------------------------------
# Resources
# ----------------------------------------------------------------------------

@mcp_server.resource("bodhan://voices")
def get_voice_catalog() -> str:
    """Bodhan Indic-Speak fixed voice library catalog by language and gender."""
    voices = {
        "hi": {"female": ["Kavya", "Suhani"], "male": ["Amit"]},
        "ta": {"female": ["Anitha"], "male": ["Arun"]},
        "bn": {"female": ["Ishita"], "male": ["Sourav"]},
        "te": {"female": ["Sravani"], "male": ["Vamsi"]},
        "mr": {"female": ["Anagha"], "male": ["Chinmay"]},
        "gu": {"female": ["Dhara"], "male": ["Parth"]},
        "kn": {"female": ["Deepika"], "male": ["Adarsh"]},
        "ml": {"female": ["Lakshmi"], "male": ["Kiran"]},
        "pa": {"female": ["Kaur"], "male": ["Manpreet"]},
        "ur": {"female": ["Saba"], "male": ["Zaid"]},
        "en": {"female": ["Kavya"], "male": ["Amit"]},
    }
    return json.dumps(voices, indent=2)


@mcp_server.resource("bodhan://pricing")
def get_pricing_card() -> str:
    """Bodhan official rate card in INR."""
    pricing = {
        "indic-transcribe": {"price": "₹0.10 per input audio minute", "unit": "minute"},
        "indic-translate": {"price": "₹0.20 per 10,000 output tokens", "unit": "10k tokens"},
        "indic-speak": {"price": "₹6.00 per 10,000 input characters", "unit": "10k characters"},
        "indic-ocr": {"price": "₹0.20 per image/page", "unit": "page"},
    }
    return json.dumps(pricing, indent=2)


# ----------------------------------------------------------------------------
# Prompts
# ----------------------------------------------------------------------------

@mcp_server.prompt("audio_summary")
def audio_summary_prompt(language: str, target_duration: str) -> str:
    """Prompt template for generating an Indic audio summary."""
    return (
        f"You need to create a {target_duration} audio summary in {language}.\n"
        "1. Extract the text using bodhan_ocr or bodhan_transcribe.\n"
        "2. Summarize the text in English to capture the core points.\n"
        f"3. Use bodhan_translate to translate the English summary into {language}.\n"
        f"4. Use bodhan_speak to generate speech audio in {language}.\n"
        "Remember: Never generate Indian-language text yourself; only use bodhan_translate."
    )


def start_server(
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    **kwargs: Any,
) -> None:
    """Start the Bodhan MCP server with chosen transport (stdio or streamable-http)."""
    if transport == "streamable-http":
        mcp_server.run(transport="streamable-http", host=host, port=port, **kwargs)
    elif transport == "sse":
        mcp_server.run(transport="sse", host=host, port=port, **kwargs)
    else:
        mcp_server.run(transport="stdio", **kwargs)


def start_stdio_server() -> None:
    """Start the MCP server over stdio transport (default)."""
    start_server(transport="stdio")


if __name__ == "__main__":
    start_stdio_server()
