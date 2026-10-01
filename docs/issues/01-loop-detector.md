# Add LoopDetector hook (doom-loop detection)

## Context
Agents get stuck repeating themselves. `LoopDetector` is a `Hook` (see `harness/hooks.py`) that spots this and aborts the run. Read `PRD.md`, `DESIGN.md` and `CONTRIBUTING.md` first.

## Files (create exactly these, touch nothing else)
- `harness/detect/__init__.py` (empty)
- `harness/detect/loops.py`
- `tests/test_loops.py`

## Interface
```python
class LoopDetector(Hook):
    def __init__(self, repeat_threshold: int = 3, cycle_window: int = 6, action: Action = Action.ABORT): ...
    def on_step(self, state: RunState, step: Step) -> Action | None: ...
```
`on_step` builds the call sequence: every `h["call"]` in `state.history` (skip entries without `"call"`, e.g. the final answer entry), then `step.tool_call` if it is not None. A call is identified by `(name, args)`; args compare equal regardless of dict key order (canonicalise with `json.dumps(args, sort_keys=True)`).

Detect either:
1. **Repeat**: the last `repeat_threshold` calls are all identical.
2. **Cycle**: within the last `cycle_window` calls, the pattern A,B,A,B,... (period 2, at least 2 full repetitions, with A != B) fills the window's tail.

On detection: `state.emit("loop", pattern="repeat" | "cycle", calls=[names of the calls involved])` and return `self.action`. Otherwise return `None`.

## Acceptance criteria
- [ ] Same call 3 times in a row (the 3rd is the current step) returns ABORT and emits one `loop` event with `pattern == "repeat"`.
- [ ] A,B,A,B returns ABORT with `pattern == "cycle"`.
- [ ] Same call twice then a different call: returns None (no false positive).
- [ ] Same call 3 times but interleaved with different calls (A,B,A,C,A): returns None.
- [ ] Args with different key order (`{"a":1,"b":2}` vs `{"b":2,"a":1}`) count as identical.
- [ ] `action=Action.PAUSE` is returned instead when configured.
- [ ] Final-answer step (`tool_call is None`) never triggers detection by itself.
- [ ] End to end: a `Runner` (see `tests/test_runner.py` for how to build one with `scripted`) with a scripted looping agent ends with status `"aborted"` and a `loop` event.
- [ ] `pytest` and `ruff check .` pass.

## Do not
- Edit `harness/types.py`, `runner.py`, `hooks.py` or any existing test.
- Add dependencies.
- Add configuration beyond the three constructor arguments.
- Look at results or output text; calls only.
