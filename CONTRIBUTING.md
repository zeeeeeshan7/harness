# Contributing (humans and coding agents)

## Setup and checks
```
pip install -e ".[dev]"
pytest
ruff check .
```
Both must pass before a PR is ready. Python >= 3.11.

## Rules
1. Read `PRD.md` and `DESIGN.md` first. Implement against the interfaces in `DESIGN.md` exactly.
2. Touch only the files listed in the issue. If you need another file, stop and say so in the PR.
3. Never change `harness/types.py`, `runner.py`, or `hooks.py` from a leaf-module issue.
4. No new dependencies. Standard library only unless the issue says otherwise.
5. No network calls in tests. Use mocks. No API keys needed or available.
6. Deterministic: take a `random.Random` or seed argument; never use the global `random` or `time` in logic.
7. Tests must assert behavior, including at least one failure or edge case. A test that cannot fail is not a test.
8. Keep it small: no extra abstractions, config, or features beyond the issue.

## PR checklist
- [ ] Only listed files changed
- [ ] New tests cover each acceptance criterion
- [ ] `pytest` and `ruff check .` pass
- [ ] PR description maps each acceptance criterion to the test that covers it
