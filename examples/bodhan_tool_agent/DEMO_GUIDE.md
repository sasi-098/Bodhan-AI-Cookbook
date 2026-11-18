# 5-Minute Demo Video Recording Guide

This guide provides a structured script to record your **5-minute (or less) demo video** for the Bodhan Take-Home submission.

---

### Video Checklist
- [ ] Duration is strictly under 5 minutes.
- [ ] No login/credentials required to view the video (upload to Loom, unlisted YouTube, or Google Drive with public link).
- [ ] Microphone audio is clear.

---

### Step-by-Step Script & Timing

#### 1. Introduction & Architecture (0:00 – 0:45)
- **What to show**: Open `README.md` in VS Code / IDE.
- **What to say**:
  > *"Hi everyone, today I'm demonstrating the Bodhan Tool Server and Autonomous Task Agent. The system consists of an MCP server wrapping Bodhan's 4 Indic models—Indic-Transcribe, Indic-Translate, Indic-Speak, and Indic-OCR—paired with a CLI task agent that plans, verifies, and executes multi-step Indic media tasks with strict budget and prompt-injection guardrails."*
- Highlight the **Architecture Mermaid diagram** in the README.

#### 2. MCP Server Standalone Demo (0:45 – 1:30)
- **What to show**: Terminal.
- **Command to run**:
  ```bash
  python -m bodhan_mcp --help
  ```
- **What to say**:
  > *"The MCP server runs independently over stdio or streamable HTTP, exposing 5 typed tools: transcribe with ≤30s chunking, translate with Indic-to-Indic English pivot, speak with sentence chunking and WAV stitching, OCR with multi-page PDF support, and a free media inspection tool. It also exposes the Indic-Speak voice catalog as an MCP resource."*

#### 3. Multi-Step Task Demo (Tamil Audio Summary) (1:30 – 2:45)
- **What to show**: Terminal and generated files.
- **Command to run**:
  ```bash
  python -m bodhan_agent --task "Make a two-minute Tamil audio summary of this chapter" --files sample_data/sample_chapter.pdf --out ./out
  ```
- **What to say**:
  > *"Now let's run the autonomous task agent. It takes a natural language task and an input chapter PDF. Notice how it plans: first it runs Indic-OCR to extract text and tables; next it creates a summary and calls Indic-Translate to produce Tamil text; then it calls Indic-Speak to synthesize speech; and finally, before finishing, it runs our verification suite to back-transcribe the audio and verify clarity."*
- **Inspect `out/` folder**:
  - Show `result.md` (summary, assumptions, links).
  - Show `trace.jsonl` (step-by-step tool latency, arguments, and cost in INR).
  - Play 2 seconds of the generated audio in `out/artifacts/`.

#### 4. Honest Failure on Impossible Task (2:45 – 3:30)
- **What to show**: Terminal.
- **Command to run**:
  ```bash
  python -m bodhan_agent --task "Translate this video into French" --files sample_data/sample_video.mp4 --out ./out_french
  ```
- **What to say**:
  > *"A critical requirement of Bodhan agents is honest failure. When asked to translate into French—which is unsupported by Indic models—the agent does not hallucinate fake output or invent translations. Instead, it exits gracefully, declares an impossible task, and writes an honest explanation in result.md at ₹0.00 cost."*
- Show `out_french/result.md`.

#### 5. Self-Evaluation Benchmark Suite & Tests (3:30 – 4:45)
- **What to show**: Terminal.
- **Command to run**:
  ```bash
  python self_eval.py
  ```
- **What to say**:
  > *"To ensure versatility and prevent regressions, we built a self-evaluation suite that tests 8 tasks: multimodal summaries, ASR subtitles, worksheet table translation, language identification, speech synthesis, unsupported languages, missing files, and budget exhaustion. As you can see, all 8 tasks pass with a 100% pass rate, and our deduplication cache ensures zero wasted tokens on repeated calls."*
- Run `pytest`:
  ```bash
  pytest tests/ -v
  ```
  > *"All 39 automated unit, integration, and architectural contract tests pass."*

#### 6. Wrap Up (4:45 – 5:00)
- **What to say**:
  > *"Everything is containerized, documented, and ready for deployment in the Bodhan AI Cookbook. Thank you!"*
