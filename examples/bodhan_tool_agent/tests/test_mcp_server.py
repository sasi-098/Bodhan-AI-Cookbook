"""Unit tests for Bodhan MCP Server registration and interfaces."""

import pytest
from bodhan_mcp.server import mcp_server


def test_server_metadata():
    assert mcp_server.name == "bodhan_mcp"
    assert "Bodhan" in mcp_server.title


def test_server_tools_registered():
    tool_names = list(mcp_server._tool_manager._tools.keys())
    expected = [
        "bodhan_transcribe",
        "bodhan_translate",
        "bodhan_speak",
        "bodhan_ocr",
        "inspect_media",
    ]
    for exp in expected:
        assert exp in tool_names, f"Expected tool '{exp}' not registered in MCPServer"


def test_server_resources_registered():
    resource_uris = list(mcp_server._resource_manager._resources.keys())
    assert "bodhan://voices" in resource_uris
    assert "bodhan://pricing" in resource_uris


def test_server_prompts_registered():
    prompt_names = list(mcp_server._prompt_manager._prompts.keys())
    assert "audio_summary" in prompt_names
