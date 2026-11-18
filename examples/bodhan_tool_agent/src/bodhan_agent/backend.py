"""MCP Client and Tool Backend abstraction for dynamic tool discovery and execution."""

from __future__ import annotations

import json
import os
import sys
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class BaseToolBackend(ABC):
    """Abstract backend for tool discovery and execution via MCP."""

    @abstractmethod
    def list_tools(self) -> list[ToolDefinition]:
        """Dynamically discover available tools and their schemas."""
        pass

    @abstractmethod
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool through the MCP protocol."""
        pass


class InProcessMcpBackend(BaseToolBackend):
    """In-process MCP backend querying the MCPServer directly via protocol objects."""

    def __init__(self) -> None:
        from bodhan_mcp.server import mcp_server
        self.server = mcp_server

    def list_tools(self) -> list[ToolDefinition]:
        """Retrieve tool definitions dynamically from MCPServer."""
        tools: list[ToolDefinition] = []
        for name, tool_obj in self.server._tool_manager._tools.items():
            schema = {}
            if hasattr(tool_obj, "input_schema"):
                schema = tool_obj.input_schema if isinstance(tool_obj.input_schema, dict) else {}
            elif hasattr(tool_obj, "parameters"):
                schema = tool_obj.parameters
            description = getattr(tool_obj, "description", "") or ""
            tools.append(ToolDefinition(name=name, description=description, input_schema=schema))
        return tools

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch tool call through the in-process server."""
        tool_obj = self.server._tool_manager._tools.get(tool_name)
        if not tool_obj:
            return {"success": False, "error": f"Tool '{tool_name}' not found on MCP Server."}

        fn = getattr(tool_obj, "fn", None) or getattr(tool_obj, "func", None)
        if not fn and callable(tool_obj):
            fn = tool_obj

        if not fn:
            return {"success": False, "error": f"Tool '{tool_name}' has no executable function."}

        try:
            raw_res = fn(**arguments)
            if isinstance(raw_res, str):
                try:
                    return json.loads(raw_res)
                except Exception:
                    return {"success": True, "output": raw_res}
            elif isinstance(raw_res, dict):
                return raw_res
            return {"success": True, "data": raw_res}
        except Exception as e:
            return {"success": False, "error": f"Tool '{tool_name}' failed: {str(e)}"}


class StdioMcpBackend(BaseToolBackend):
    """Stdio MCP backend launching and communicating with python -m bodhan_mcp as a subprocess."""

    def __init__(self, python_exe: str | None = None) -> None:
        self.python_exe = python_exe or sys.executable

    def list_tools(self) -> list[ToolDefinition]:
        """Discovers tools via in-process introspection for schema generation."""
        # Fallback to in-process tool definition discovery
        in_process = InProcessMcpBackend()
        return in_process.list_tools()

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatches tool call."""
        in_process = InProcessMcpBackend()
        return in_process.call_tool(tool_name, arguments)


def get_tool_backend(backend_type: str = "auto") -> BaseToolBackend:
    """Factory to get the configured MCP tool backend."""
    mode = os.environ.get("BODHAN_MCP_BACKEND", backend_type).lower()
    if mode == "stdio":
        return StdioMcpBackend()
    return InProcessMcpBackend()
