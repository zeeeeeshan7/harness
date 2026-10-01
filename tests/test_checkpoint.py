import pytest

from harness.checkpoint import Checkpoint
from harness.runner import Runner
from harness.types import Budget, ToolResult
from tests.conftest import call, finish, scripted

STEPS = [call("a"), call("b"), call("c"), finish("final")]
BIG = Budget(50, 100)


def tool(c):
    return ToolResult(True, c.name)


def test_load_missing_is_none(tmp_path):
    assert Checkpoint(tmp_path / "nope.jsonl").load() is None


def test_crash_and_resume_matches_uninterrupted(tmp_path):
    clean = Runner(scripted(STEPS), tool, BIG).run()
    ck = Checkpoint(tmp_path / "run.jsonl")

    def crashy(state):
        if state.step == 2:
            raise RuntimeError("kill -9")
        return STEPS[state.step]

    with pytest.raises(RuntimeError):
        Runner(crashy, tool, BIG, checkpoint=ck).run()

    ran = []
    resumed = Runner(scripted(STEPS), lambda c: ran.append(c.name) or tool(c), BIG, checkpoint=ck).run()
    assert resumed.answer == clean.answer
    assert resumed.state.history == clean.state.history
    assert resumed.total_usd == pytest.approx(clean.total_usd)
    assert ran == ["c"]  # steps a and b not replayed
    assert any(e.kind == "resume" for e in resumed.events)


def test_truncated_last_line_ignored(tmp_path):
    p = tmp_path / "run.jsonl"
    ck = Checkpoint(p)
    Runner(scripted(STEPS), tool, BIG, checkpoint=ck).run()
    good = ck.load().step
    with p.open("a") as f:
        f.write('{"step": 99, "hist')  # crash mid-write
    assert ck.load().step == good
