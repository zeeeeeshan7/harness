# Harness: Design

Python >= 3.11. Stdlib only for core. Tests: pytest. Lint: ruff.

## Layout
```
harness/
  types.py        # Step, Event, ToolCall, ToolResult, RunState, Budget
  runner.py       # Runner: the loop
  hooks.py        # Hook protocol + HookResult
  checkpoint.py   # JSONL checkpoint, resume
  cost.py         # CostMeter hook
  detect/loops.py # LoopDetector hook
  chaos.py        # ChaosHook (seeded fault injection)
  report.py       # render_report(events) -> str
  steer/telegram.py
  cli.py
tests/
```

## Core types (the contract; changing these needs the owner's approval)
```python
@dataclass(frozen=True)
class ToolCall:   name: str; args: dict
@dataclass(frozen=True)
class ToolResult: ok: bool; output: str; error: str | None = None
@dataclass(frozen=True)
class Budget:     max_steps: int; max_usd: float

@dataclass
class Step:                       # one agent turn, returned by the caller's step_fn
    tool_call: ToolCall | None    # None = agent finished
    answer: str | None
    cost_usd: float
    tokens_in: int
    tokens_out: int

@dataclass(frozen=True)
class Event:                      # append-only log, source for report + checkpoint
    kind: str                     # "step" | "tool_result" | "fault" | "loop" | "abort" | "resume" | "done"
    step: int
    data: dict
    ts: float

class Action(Enum): CONTINUE; ABORT; PAUSE
```

## Runner
```python
Runner(step_fn, tool_fn, budget, hooks=[], checkpoint=None)
runner.run(state=None) -> RunResult   # RunResult: status, answer, events, total_usd
```
Loop: `step_fn(state) -> Step`, then hooks `on_step`, then `tool_fn(call) -> ToolResult` wrapped by hooks `on_tool_call` / `on_tool_result`, append events, checkpoint, check budget. Stops on: answer, step limit, usd limit, hook ABORT.

## Hooks
```python
class Hook(Protocol):
    def on_step(self, state, step) -> Action | None: ...
    def on_tool_call(self, state, call) -> ToolCall | ToolResult | None: ...   # return a ToolResult to short-circuit (chaos)
    def on_tool_result(self, state, call, result) -> ToolResult | None: ...    # return a new result to replace it
```
Every method is optional (default no-op). Hooks must not mutate `state`. They emit events via `state.emit(...)`.

## Checkpoint
One JSON line per step: full `RunState` (step index, message history, total cost, events so far). Resume loads the last valid line (a truncated last line is ignored) and continues at step+1. Tool calls are not replayed.

## Determinism
All randomness comes from a `random.Random(seed)` passed in. No global `random`, no wall-clock in logic (timestamps only in `Event.ts`).

## Testing
Mock `step_fn` scripted from a list. No network in the default test run. Real-model tests are marked `slow`.

## EvalForge scoring (v1.0, owner-built)
`recovery_score(events) -> float`, bootstrap CI via EvalForge. Interface TBD, see PRD open questions.
