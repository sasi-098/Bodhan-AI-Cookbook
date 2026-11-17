"""Autonomous Task Agent orchestrating Bodhan tools with budget and verification."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from bodhan_mcp.cost import CostTracker
from bodhan_mcp.tools.inspect_tool import run_inspect_media
from bodhan_mcp.tools.ocr import run_ocr
from bodhan_mcp.tools.speak import run_speak
from bodhan_mcp.tools.transcribe import run_transcribe
from bodhan_mcp.tools.translate import run_translate

from bodhan_agent.llm import llm_client
from bodhan_agent.reporter import RunReporter
from bodhan_agent.verifier import artifact_verifier


class TaskAgent:
    """The Autonomous Bodhan Task Agent."""

    def __init__(
        self,
        task: str,
        files: list[str | Path] | None = None,
        out_dir: str | Path = "./out",
        max_steps: int = 30,
        max_cost_inr: float = 20.0,
    ):
        self.task = task
        self.input_files = self._resolve_input_files(files or [])
        self.out_dir = Path(out_dir).resolve()
        self.max_steps = max_steps
        self.max_cost_inr = max_cost_inr

        self.cost_tracker = CostTracker(max_cost_inr=self.max_cost_inr)
        self.reporter = RunReporter(self.out_dir)
        self.history: list[dict[str, Any]] = []

    def _resolve_input_files(self, paths: list[str | Path]) -> list[Path]:
        """Resolve files or scan directories passed to --files."""
        resolved: list[Path] = []
        for p_str in paths:
            p = Path(p_str)
            if p.is_dir():
                for item in p.rglob("*"):
                    if item.is_file() and not item.name.startswith("."):
                        resolved.append(item.resolve())
            elif p.is_file():
                resolved.append(p.resolve())
        return resolved

    def _dispatch_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a tool call to the corresponding Bodhan tool implementation."""
        t0 = time.time()
        tool_map = {
            "bodhan_transcribe": run_transcribe,
            "bodhan_translate": run_translate,
            "bodhan_speak": run_speak,
            "bodhan_ocr": run_ocr,
            "inspect_media": run_inspect_media,
        }

        func = tool_map.get(tool_name)
        if not func:
            return {
                "success": False,
                "error": f"Unknown tool '{tool_name}'. Available: {list(tool_map.keys())}",
                "cost_inr": 0.0,
                "latency_seconds": round(time.time() - t0, 2),
            }

        try:
            result = func(**arguments)
            cost = float(result.get("cost_inr", 0.0))

            # Record in cost tracker
            if cost > 0:
                self.cost_tracker.record_cost(
                    model=tool_name,
                    operation=tool_name,
                    metric="inr",
                    quantity=cost,
                    cost_inr=cost,
                    timestamp=time.time(),
                )

            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}",
                "cost_inr": 0.0,
                "latency_seconds": round(time.time() - t0, 2),
            }

    def run(self) -> dict[str, Any]:
        """Execute the agent loop: Plan -> Act -> Verify -> Report."""
        start_time = time.time()
        status = "running"
        final_answer = ""
        assumptions: list[str] = []
        candidate_artifacts: list[str] = []
        impossible_reason: str | None = None
        error_msg: str | None = None

        step = 0
        while step < self.max_steps:
            step += 1

            # Check budget
            if self.cost_tracker.is_budget_exceeded():
                status = "budget_exceeded"
                error_msg = f"Budget limit of ₹{self.max_cost_inr:.2f} INR reached."
                break

            # Ask LLM / Planner for next step
            decision = llm_client.plan_next_step(
                task=self.task,
                files=self.input_files,
                history=self.history,
                step_number=step,
            )

            plan_thought = decision.get("thought", "")

            # 1. Impossible Task handling
            if decision.get("impossible_task"):
                status = "impossible_task"
                impossible_reason = decision.get("reason", "Task cannot be completed with available tools.")
                final_answer = impossible_reason
                break

            # 2. Final Answer handling
            if "final_answer" in decision:
                status = "completed"
                final_answer = decision.get("final_answer", "")
                assumptions = decision.get("assumptions", [])
                candidate_artifacts = decision.get("artifacts", [])
                break

            # 3. Tool Call handling
            tool_name = decision.get("tool")
            arguments = decision.get("arguments", {})

            if not tool_name:
                status = "completed"
                final_answer = plan_thought or "Task finished with no further tool calls required."
                break

            tool_start = time.time()
            tool_result = self._dispatch_tool(tool_name, arguments)
            latency = time.time() - tool_start
            cost = float(tool_result.get("cost_inr", 0.0))

            # Result summary
            if tool_name == "bodhan_transcribe":
                summary = f"Transcribed {tool_result.get('duration_seconds', 0)}s audio: '{tool_result.get('text', '')[:80]}...'"
            elif tool_name == "bodhan_translate":
                summary = f"Translated text into {tool_result.get('target_lang')}: '{tool_result.get('translation', '')[:80]}...'"
            elif tool_name == "bodhan_speak":
                audio_path = tool_result.get("audio_file", "")
                summary = f"Synthesized speech audio ({tool_result.get('duration_seconds', 0)}s) to {audio_path}"
                if audio_path:
                    candidate_artifacts.append(audio_path)
            elif tool_name == "bodhan_ocr":
                summary = f"OCR processed {tool_result.get('page_count', 0)} pages, extracted {len(tool_result.get('blocks', []))} layout blocks."
            else:
                summary = f"Inspected file: {tool_result.get('file_type', 'unknown')}"

            # Log trace step
            self.reporter.log_trace_step(
                step=step,
                plan=plan_thought,
                tool=tool_name,
                arguments=arguments,
                result_summary=summary,
                latency_seconds=latency,
                cost_inr=cost,
            )

            # Record in history
            self.history.append({
                "step": step,
                "plan": plan_thought,
                "tool": tool_name,
                "arguments": arguments,
                "result_summary": summary,
                "data": tool_result,
            })

        if status == "running":
            status = "max_steps_reached"

        total_time = time.time() - start_time
        cost_summary = self.cost_tracker.get_summary()

        # Collect & move artifacts
        final_artifacts = self.reporter.collect_artifacts(candidate_artifacts)

        # Verification step
        verification_results: dict[str, Any] = {"verified_count": 0, "all_passed": True, "checks": []}
        if status == "completed" and final_artifacts:
            verification_results = artifact_verifier.verify_artifacts(final_artifacts)

        # Write reports
        self.reporter.write_result_md(
            task=self.task,
            status=status,
            final_answer=final_answer,
            assumptions=assumptions,
            artifacts=final_artifacts,
            total_cost=cost_summary["total_cost_inr"],
            total_time=total_time,
            impossible_reason=impossible_reason,
        )

        self.reporter.write_report_json(
            task=self.task,
            status=status,
            steps_count=step,
            total_cost=cost_summary["total_cost_inr"],
            total_time=total_time,
            cost_by_model=cost_summary["cost_by_model"],
            verification_results=verification_results,
            artifacts=final_artifacts,
            error=error_msg,
        )

        return {
            "status": status,
            "final_answer": final_answer,
            "artifacts": [str(a) for a in final_artifacts],
            "total_cost_inr": cost_summary["total_cost_inr"],
            "total_time_seconds": round(total_time, 2),
            "verification": verification_results,
        }
