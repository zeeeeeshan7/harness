# Add ChaosHook (seeded fault injection)

## Context
To test resilience we inject tool failures on purpose. `ChaosHook` is a `Hook` (see `harness/hooks.py`) that makes tool calls time out, drop, or return corrupted output, deterministically from a seed. Read `PRD.md`, `DESIGN.md` and `CONTRIBUTING.md` first.

## Files (create exactly these, touch nothing else)
- `harness/chaos.py`
- `tests/test_chaos.py`

## Interface
```python
class ChaosHook(Hook):
    def __init__(self, seed: int, p_timeout: float = 0.0, p_drop: float = 0.0, p_malformed: float = 0.0): ...
    injected: list[tuple[int, str]]   # (step, fault kind) in order
    def on_tool_call(self, state, call) -> ToolResult | None: ...
    def on_tool_result(self, state, call, result) -> ToolResult | None: ...
```
- `__init__` raises `ValueError` if any probability is outside [0, 1] or the three sum to more than 1.
- Own a `random.Random(seed)`. In `on_tool_call`, draw exactly **one** `u = rng.random()` per tool call, then pick: `u < p_timeout` is a timeout; else `u < p_timeout + p_drop` is a drop; else `u < p_timeout + p_drop + p_malformed` is malformed; else no fault.
- **timeout**: return `ToolResult(False, "", "TimeoutError: tool timed out")` (the real tool is skipped).
- **drop**: return `ToolResult(False, "", "ConnectionError: connection dropped")` (tool skipped).
- **malformed**: return `None` from `on_tool_call` (tool runs normally); remember the fault, and in `on_tool_result` return `ToolResult(True, result.output[: len(result.output) // 2] + "�{")`.
- For every fault: `state.emit("fault", kind="timeout" | "drop" | "malformed", tool=call.name)` and append `(state.step, kind)` to `self.injected`. Emit malformed in `on_tool_call` when it is chosen.
- No fault means return `None` from both methods.

## Acceptance criteria
- [ ] Same seed and same sequence of calls gives identical `injected` lists; different seeds give different ones (use 50 calls, p=0.3 each).
- [ ] All probabilities 0 injects nothing and never changes a result.
- [ ] `p_timeout=1.0` makes every call return the timeout result and the real tool is never invoked (verify with a Runner and a tool that records calls).
- [ ] `p_drop=1.0` likewise for drop.
- [ ] `p_malformed=1.0`: the tool runs, and the result output is corrupted exactly as specified.
- [ ] Over 2000 calls with `p_timeout=0.2, p_drop=0.1, p_malformed=0.1`, observed fault frequencies are within 0.03 of the probabilities.
- [ ] A `fault` event is emitted per fault, with the right `kind`.
- [ ] Constructor `ValueError` cases (negative p, sum > 1) are tested.
- [ ] Exactly one `rng.random()` draw per tool call (assert by seeding two hooks and comparing, or by patching).
- [ ] `pytest` and `ruff check .` pass.

## Do not
- Edit `harness/types.py`, `runner.py`, `hooks.py` or any existing test.
- Use the global `random` module or `time`.
- Add retries, delays or sleeping; faults are instant.
- Add dependencies.
