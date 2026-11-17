"""Entrypoint for running Bodhan MCP Server over stdio or streamable-http."""

import argparse
import sys

from bodhan_mcp.server import start_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bodhan MCP Tool Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="MCP transport protocol.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind for HTTP/SSE transports.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on for HTTP/SSE transports.",
    )

    args = parser.parse_args(argv)

    if args.transport != "stdio":
        print(f"Starting Bodhan MCP Server on {args.transport}://{args.host}:{args.port}")

    start_server(transport=args.transport, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
