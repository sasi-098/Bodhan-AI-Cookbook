"""Command-line interface for the Bodhan Task Agent.

Usage:
    python -m bodhan_agent \
      --task "Make a two-minute Tamil audio summary of this chapter" \
      --files path/to/inputs/ \
      --out ./out \
      [--max-steps 30] [--max-cost-inr 20]
"""

from __future__ import annotations

import argparse
import sys

from bodhan_agent.agent import TaskAgent
from bodhan_agent.backend import get_tool_backend


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bodhan Autonomous Task Agent for Indic language processing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--task",
        required=True,
        type=str,
        help="Natural language instruction for the agent.",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=[],
        help="Path(s) to input files or directory containing input files.",
    )
    parser.add_argument(
        "--out",
        default="./out",
        type=str,
        help="Output directory where result.md, report.json, trace.jsonl, and artifacts are written.",
    )
    parser.add_argument(
        "--max-steps",
        default=30,
        type=int,
        help="Maximum number of execution steps before stopping.",
    )
    parser.add_argument(
        "--max-cost-inr",
        default=20.0,
        type=float,
        help="Maximum allowed budget in INR.",
    )
    parser.add_argument(
        "--timeout-seconds",
        default=300.0,
        type=float,
        help="Wall-clock execution timeout in seconds.",
    )
    parser.add_argument(
        "--backend",
        choices=["inprocess", "stdio"],
        default="inprocess",
        help="MCP backend to use for dynamic tool discovery and execution.",
    )

    args = parser.parse_args(argv)

    print("=== Bodhan Task Agent Starting ===")
    print(f"Task: {args.task}")
    print(f"Inputs: {args.files}")
    print(f"Output directory: {args.out}")
    print(f"Max steps: {args.max_steps} | Max budget: ₹{args.max_cost_inr:.2f} INR | Timeout: {args.timeout_seconds}s")
    print(f"MCP Backend: {args.backend}")

    agent = TaskAgent(
        task=args.task,
        files=args.files,
        out_dir=args.out,
        max_steps=args.max_steps,
        max_cost_inr=args.max_cost_inr,
        timeout_seconds=args.timeout_seconds,
        backend=get_tool_backend(args.backend),
    )

    result = agent.run()

    print("\n=== Task Execution Finished ===")
    print(f"Status: {result['status']}")
    print(f"Total Cost: ₹{result['total_cost_inr']:.4f} INR")
    print(f"Time: {result['total_time_seconds']}s")
    print(f"Artifacts produced: {len(result['artifacts'])}")
    print(f"Results written to: {args.out}/result.md")

    if result["status"] == "impossible_task":
        # Honest failure on impossible task is considered a successful detection
        return 0
    elif result["status"] in ("completed", "max_steps_reached"):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
