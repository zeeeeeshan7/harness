# Harness: PRD

## Problem
Long-running LLM agents fail in ways a happy-path eval never shows: they loop, overspend, hang on tool timeouts, choke on malformed output, and lose all progress on a crash. Harness is a runner that wraps any agent loop, makes those failures survivable, and measures how well the agent recovers.

## Goals
1. Run an agent loop with hard step and dollar budgets.
2. Show live cost while running.
3. Detect doom loops (repeated calls, no progress) and abort or intervene.
4. Checkpoint every step and resume after a crash with no repeated work.
5. Chaos mode: seeded, deterministic fault injection (tool timeouts, malformed output, dropped connections).
6. Score recovery (did the agent finish the task despite faults) via EvalForge's bootstrap.
7. Emit a resilience report (markdown).
8. Steer a live run from Telegram (pause, resume, abort).

## Non-goals
- Not an agent framework. Harness wraps a caller-supplied step function.
- No web UI. No multi-agent orchestration. No provider abstraction beyond what the caller passes in.
- No new dependencies without a stated reason.

## Users
Just me, running agents from the CLI. Real runs use DeepSeek (Anthropic-compatible endpoint) for cost.

## Success criteria
- `harness run` completes a chaos scenario end to end on a mock model, in CI, with no network.
- A run killed mid-way resumes and produces the same final result as an uninterrupted run (seeded).
- The resilience report for one real-model run is readable and goes in the README.

## Milestones
- v0.1: runner core, hooks, checkpoint/resume, cost meter (built locally).
- v0.2: loop detector, chaos mode, report, Telegram (built via Copilot issues).
- v1.0: EvalForge recovery scoring, CLI wiring, README demo.

## Open questions
- EvalForge bootstrap interface: exact function signature to be filled in before the scoring issue.
