"""Self-evaluation benchmark suite for the Bodhan Task Agent.

Runs a suite of multi-step and edge-case tasks and calculates pass rates,
honest failure rates, verification scores, and total cost.

Usage:
    python self_eval.py [--out-dir outputs/evaluation]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from bodhan_agent.agent import TaskAgent

BENCHMARK_TASKS = [
    {
        "id": "task_1_tamil_summary",
        "description": "Multi-step document OCR, English summary, Tamil translation, and speech synthesis.",
        "task": "Make a two-minute Tamil audio summary of this chapter",
        "files": ["sample_data/sample_chapter.pdf"],
        "expected_status": "completed",
        "expected_artifacts": [".wav"],
    },
    {
        "id": "task_2_hindi_subtitles",
        "description": "Audio transcription with chunking, translation into English, and SRT generation.",
        "task": "Transcribe this Hindi voice note and give me English subtitles",
        "files": ["sample_data/hindi_voice_note.wav"],
        "expected_status": "completed",
        "expected_artifacts": [".srt"],
    },
    {
        "id": "task_3_marathi_worksheet",
        "description": "Worksheet table extraction and translation to Marathi preserving table structure.",
        "task": "Translate this worksheet into Marathi and keep the table",
        "files": ["sample_data/worksheet_math.png"],
        "expected_status": "completed",
        "expected_artifacts": [".md"],
    },
    {
        "id": "task_4_telugu_clips",
        "description": "Multi-audio language identification and translation of target clips.",
        "task": "Which of these clips are in Telugu? Translate those into English",
        "files": ["sample_data/clips"],
        "expected_status": "completed",
        "expected_artifacts": [],
    },
    {
        "id": "task_5_bengali_speech",
        "description": "Text paragraph narration in Bengali with specified female voice.",
        "task": "Read this paragraph aloud in Bengali with a female voice",
        "files": ["sample_data/bengali_paragraph.txt"],
        "expected_status": "completed",
        "expected_artifacts": [".wav"],
    },
    {
        "id": "task_6_french_impossible",
        "description": "Honest failure on unsupported language (French) with zero hallucinated output.",
        "task": "Translate this video into French",
        "files": ["sample_data/sample_video.mp4"],
        "expected_status": "impossible_task",
        "expected_artifacts": [],
    },
    {
        "id": "task_7_missing_files_impossible",
        "description": "Honest failure on missing required input files.",
        "task": "Transcribe this audio file and translate it",
        "files": [],
        "expected_status": "impossible_task",
        "expected_artifacts": [],
    },
    {
        "id": "task_8_budget_enforcement",
        "description": "Graceful stoppage and partial work reporting when budget is exhausted.",
        "task": "Make a two-minute Tamil audio summary of this chapter",
        "files": ["sample_data/sample_chapter.pdf"],
        "max_cost_inr": 0.0001,
        "expected_status": "budget_exceeded",
        "expected_artifacts": [],
    },
]


def run_self_evaluation(output_dir: str | Path = "outputs/evaluation") -> dict[str, Any]:
    out_root = Path(output_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("        BODHAN TASK AGENT SELF-EVALUATION BENCHMARK SUITE")
    print("=" * 70)

    results: list[dict[str, Any]] = []
    total_passed = 0
    total_cost_inr = 0.0
    start_eval_time = time.time()

    for item in BENCHMARK_TASKS:
        task_id = item["id"]
        task_prompt = item["task"]
        expected_status = item["expected_status"]
        max_cost = item.get("max_cost_inr", 20.0)

        task_out_dir = out_root / task_id

        # Resolve files relative to recipe directory
        recipe_dir = Path(__file__).resolve().parent
        file_paths = [recipe_dir / f for f in item["files"]]

        print(f"\n▶ Running [{task_id}]...")
        print(f"  Prompt: \"{task_prompt}\"")

        agent = TaskAgent(
            task=task_prompt,
            files=file_paths,
            out_dir=task_out_dir,
            max_cost_inr=max_cost,
        )

        res = agent.run()

        status = res["status"]
        cost = res["total_cost_inr"]
        duration = res["total_time_seconds"]
        artifacts = res["artifacts"]
        verification = res.get("verification", {})

        total_cost_inr += cost

        # Verification check
        status_match = status == expected_status
        artifacts_match = True
        for ext in item.get("expected_artifacts", []):
            if not any(a.endswith(ext) for a in artifacts):
                artifacts_match = False

        passed = status_match and artifacts_match and verification.get("all_passed", True)

        if passed:
            total_passed += 1
            verdict = "PASS"
        else:
            verdict = "FAIL"

        print(f"  Result: [{verdict}] (Status: {status}, Cost: ₹{cost:.4f}, Time: {duration}s, Artifacts: {len(artifacts)})")

        results.append({
            "task_id": task_id,
            "description": item["description"],
            "prompt": task_prompt,
            "expected_status": expected_status,
            "actual_status": status,
            "cost_inr": cost,
            "latency_seconds": duration,
            "artifacts_count": len(artifacts),
            "verification_passed": verification.get("all_passed", True),
            "passed": passed,
        })

    total_time = round(time.time() - start_eval_time, 2)
    pass_rate = round((total_passed / len(BENCHMARK_TASKS)) * 100.0, 1)

    print("\n" + "=" * 70)
    print("                     BENCHMARK SUMMARY SCORECARD")
    print("=" * 70)
    print(f"Total Tasks Evaluated:  {len(BENCHMARK_TASKS)}")
    print(f"Passed:                 {total_passed}")
    print(f"Failed:                 {len(BENCHMARK_TASKS) - total_passed}")
    print(f"Pass Rate:              {pass_rate}%")
    print(f"Total Billed Cost:      ₹{total_cost_inr:.4f} INR")
    print(f"Total Evaluation Time:  {total_time}s")
    print("=" * 70)

    scorecard = {
        "summary": {
            "total_tasks": len(BENCHMARK_TASKS),
            "passed_tasks": total_passed,
            "failed_tasks": len(BENCHMARK_TASKS) - total_passed,
            "pass_rate_percentage": pass_rate,
            "total_cost_inr": round(total_cost_inr, 4),
            "total_time_seconds": total_time,
            "timestamp": time.time(),
        },
        "tasks": results,
    }

    scorecard_path = out_root / "eval_scorecard.json"
    scorecard_path.write_text(json.dumps(scorecard, indent=2), encoding="utf-8")
    print(f"\nDetailed scorecard saved to: {scorecard_path}")

    return scorecard


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bodhan Task Agent Self-Evaluation")
    parser.add_argument("--out-dir", default="outputs/evaluation", help="Directory for evaluation results")
    args = parser.parse_args()
    run_self_evaluation(args.out_dir)
