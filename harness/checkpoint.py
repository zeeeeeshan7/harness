from __future__ import annotations

import json
from pathlib import Path

from harness.types import RunState


class Checkpoint:
    """JSONL, one full RunState per line. Load takes the last line that parses."""

    def __init__(self, path):
        self.path = Path(path)

    def save(self, state: RunState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(state.to_dict()) + "\n")

    def load(self) -> RunState | None:
        if not self.path.exists():
            return None
        for line in reversed(self.path.read_text(encoding="utf-8").splitlines()):
            try:
                return RunState.from_dict(json.loads(line))
            except (ValueError, KeyError, TypeError):
                continue  # truncated or corrupt tail, try the previous line
        return None
