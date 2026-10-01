from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: str
    error: str | None = None


@dataclass(frozen=True)
class Budget:
    max_steps: int
    max_usd: float


@dataclass
class Step:
    """One agent turn, returned by the caller's step_fn. tool_call None = agent finished."""

    tool_call: ToolCall | None
    answer: str | None
    cost_usd: float
    tokens_in: int
    tokens_out: int


@dataclass(frozen=True)
class Event:
    kind: str  # step | tool_result | fault | loop | abort | pause | resume | done
    step: int
    data: dict
    ts: float


class Action(Enum):
    CONTINUE = "continue"
    ABORT = "abort"
    PAUSE = "pause"


@dataclass
class RunState:
    step: int = 0  # completed steps
    history: list = field(default_factory=list)
    total_usd: float = 0.0
    events: list = field(default_factory=list)

    def emit(self, kind: str, **data) -> Event:
        e = Event(kind, self.step, data, time.time())
        self.events.append(e)
        return e

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> RunState:
        return cls(d["step"], d["history"], d["total_usd"], [Event(**e) for e in d["events"]])


@dataclass
class RunResult:
    status: str  # done | max_steps | max_usd | aborted | paused
    answer: str | None
    state: RunState

    @property
    def events(self):
        return self.state.events

    @property
    def total_usd(self):
        return self.state.total_usd
