# Add resilience report renderer

## Context
After a run (usually a chaos run) we want a short markdown report: what went wrong and whether the agent recovered. Pure function over the event log. Read `PRD.md`, `DESIGN.md` and `CONTRIBUTING.md` first. Event kinds are in `harness/types.py`.

## Files (create exactly these, touch nothing else)
- `harness/report.py`
- `tests/test_report.py`
- `tests/golden/report_basic.md`

## Interface
```python
def render_report(events: list[Event], title: str = "Resilience report") -> str: ...
```
Returns markdown. It must not print timestamps (`Event.ts`), so output is deterministic.

## Output format (exact)
```
# {title}

## Summary
- Outcome: {outcome}
- Steps: {n_steps}
- Cost: ${total:.4f}
- Faults injected: {n_faults}
- Loops detected: {n_loops}
- Resumes: {n_resumes}
- Recovered: {yes | no | n/a}

## Faults
| Step | Kind | Tool |
|-----:|------|------|
| 2 | timeout | search |

## Loops
| Step | Pattern |
|-----:|---------|
| 7 | repeat |
```
- `Steps` = count of `step` events. `Cost` = sum of `data["cost_usd"]` over `step` events.
- `Outcome`: `done` if a `done` event exists, else `aborted` if an `abort` event, else `paused` if a `pause` event, else `incomplete`.
- `Faults` rows come from `fault` events (`data["kind"]`, `data["tool"]`); `Loops` rows from `loop` events (`data["pattern"]`). Each section's table is replaced by the line `None.` when it has no rows. Rows in event order.
- `Recovered`: `n/a` when there are no faults; `yes` when there are faults and a `done` event after the first fault; otherwise `no`.
- Output ends with a single trailing newline.

## Acceptance criteria
- [ ] Golden-file test: a fixed list of events (built in the test with fixed `ts=0.0`) renders to exactly the contents of `tests/golden/report_basic.md`. Include 2 faults, 1 loop, 1 resume and a `done` event in that fixture.
- [ ] No faults: `Recovered: n/a` and `Faults` section shows `None.`.
- [ ] Faults and no `done` event: `Recovered: no`, `Outcome: aborted` when an `abort` event exists.
- [ ] Empty event list renders without error (`Outcome: incomplete`, zero counts).
- [ ] Changing only `ts` values does not change the output.
- [ ] `pytest` and `ruff check .` pass.

## Do not
- Edit `harness/types.py`, `runner.py`, `hooks.py` or any existing test.
- Read files or the network; the function takes events and returns a string.
- Add dependencies, templating libraries, colours or extra sections.
