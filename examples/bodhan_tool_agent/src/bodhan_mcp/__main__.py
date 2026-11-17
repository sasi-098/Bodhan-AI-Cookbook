"""Entrypoint for running Bodhan MCP Server over stdio."""

from bodhan_mcp.server import start_stdio_server

if __name__ == "__main__":
    start_stdio_server()
