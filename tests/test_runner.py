import pytest

from harness.hooks import Hook
from harness.runner import Runner
from harness.types import Action, Budget, ToolCall, ToolResult
from tests.conftest import call, finish, scripted

BIG = Budget(max_steps=50, max_usd=100)


def ok_tool(c):
    return ToolResult(True, f"ran {c.name}")


def test_finishes_with_answer():
    r = Runner(scripted([call(), call(), finish("42")]), ok_tool, BIG).run()
    assert (r.status, r.answer) == ("done", "42")
    assert r.total_usd == pytest.approx(0.03)


def test_tool_result_reaches_history():
    r = Runner(scripted([call("x", a=1), finish()]), ok_tool, BIG).run()
    h = r.state.history[0]
    assert h["call"] == {"name": "x", "args": {"a": 1}}
    assert h["result"]["output"] == "ran x"


def test_max_steps():
    r = Runner(scripted([call()] * 10), ok_tool, Budget(3, 100)).run()
    assert r.status == "max_steps"
    assert sum(e.kind == "step" for e in r.events) == 3


def test_max_usd():
    r = Runner(scripted([call(cost=1.0)] * 10), ok_tool, Budget(50, 2.5)).run()
    assert r.status == "max_usd"
    assert r.total_usd == pytest.approx(3.0)  # checked between steps, so may overshoot by one step


def test_tool_exception_becomes_failed_result():
    def boom(c):
        raise TimeoutError("slow")

    r = Runner(scripted([call(), finish()]), boom, BIG).run()
    assert r.status == "done"
    res = [e for e in r.events if e.kind == "tool_result"][0]
    assert res.data["ok"] is False and "slow" in res.data["error"]


def test_hook_abort():
    class Stop(Hook):
        def on_step(self, state, step):
            return Action.ABORT if state.step == 1 else None

    r = Runner(scripted([call()] * 5), ok_tool, BIG, hooks=[Stop()]).run()
    assert r.status == "aborted"
    assert r.events[-1].kind == "abort"


def test_hook_short_circuits_tool_call():
    class Fail(Hook):
        def on_tool_call(self, state, c):
            return ToolResult(False, "", "injected")

    calls = []
    r = Runner(scripted([call(), finish()]), lambda c: calls.append(c) or ok_tool(c), BIG, hooks=[Fail()]).run()
    assert calls == []
    assert r.state.history[0]["result"]["error"] == "injected"


def test_hook_replaces_call_and_result():
    class Swap(Hook):
        def on_tool_call(self, state, c):
            return ToolCall("swapped", {})

        def on_tool_result(self, state, c, res):
            return ToolResult(True, res.output + "!")

    r = Runner(scripted([call(), finish()]), ok_tool, BIG, hooks=[Swap()]).run()
    out = [e for e in r.events if e.kind == "tool_result"][0].data["output"]
    assert out == "ran swapped!"


def test_pause_then_resume_same_state():
    class PauseOnce(Hook):
        done = False

        def on_step(self, state, step):
            if state.step == 1 and not self.done:
                self.done = True
                return Action.PAUSE

    runner = Runner(scripted([call(), call(), finish("z")]), ok_tool, BIG, hooks=[PauseOnce()])
    r1 = runner.run()
    assert r1.status == "paused"
    r2 = runner.run(r1.state)
    assert (r2.status, r2.answer) == ("done", "z")
