from __future__ import annotations

from dataclasses import asdict

from harness.types import Action, Budget, RunResult, RunState, ToolCall, ToolResult


class Runner:
    def __init__(self, step_fn, tool_fn, budget: Budget, hooks=(), checkpoint=None):
        self.step_fn, self.tool_fn, self.budget = step_fn, tool_fn, budget
        self.hooks, self.checkpoint = list(hooks), checkpoint

    def run(self, state: RunState | None = None) -> RunResult:
        if state is None:
            state = self.checkpoint.load() if self.checkpoint else None
            if state is not None:
                state.emit("resume", from_step=state.step)
            else:
                state = RunState()
        while True:
            if state.step >= self.budget.max_steps:
                return self._stop(state, "max_steps")
            if state.total_usd >= self.budget.max_usd:
                return self._stop(state, "max_usd")

            step = self.step_fn(state)
            state.total_usd += step.cost_usd  # spent even if a hook then aborts or pauses
            state.emit("step", cost_usd=step.cost_usd, tokens_in=step.tokens_in, tokens_out=step.tokens_out)

            action = self._on_step(state, step)
            if action is Action.ABORT:
                return self._stop(state, "aborted", kind="abort")
            if action is Action.PAUSE:
                # ponytail: the paused step re-runs (and is paid for again) on resume; no replay cache
                return self._stop(state, "paused", kind="pause")

            if step.tool_call is None:
                state.history.append({"answer": step.answer})
                state.emit("done", answer=step.answer)
                state.step += 1
                self._save(state)
                return RunResult("done", step.answer, state)

            call, result = self._run_tool(state, step.tool_call)
            state.emit("tool_result", name=call.name, **asdict(result))
            state.history.append({"call": asdict(call), "result": asdict(result)})
            state.step += 1
            self._save(state)

    def _on_step(self, state, step):
        for h in self.hooks:
            a = h.on_step(state, step)
            if a in (Action.ABORT, Action.PAUSE):
                return a
        return None

    def _run_tool(self, state, call: ToolCall):
        result = None
        for h in self.hooks:
            r = h.on_tool_call(state, call)
            if isinstance(r, ToolResult):
                result = r
                break
            if isinstance(r, ToolCall):
                call = r
        if result is None:
            try:
                result = self.tool_fn(call)
            except Exception as e:  # noqa: BLE001 - a failing tool is data for the agent, not a crash
                result = ToolResult(False, "", f"{type(e).__name__}: {e}")
        for h in self.hooks:
            r = h.on_tool_result(state, call, result)
            if r is not None:
                result = r
        return call, result

    def _stop(self, state, status, kind=None):
        if kind:
            state.emit(kind)
        self._save(state)
        return RunResult(status, None, state)

    def _save(self, state):
        if self.checkpoint:
            self.checkpoint.save(state)
