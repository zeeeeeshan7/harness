from harness.cost import CostMeter
from harness.runner import Runner
from harness.types import Budget, ToolResult
from tests.conftest import call, finish, scripted


def test_meter_reports_each_step():
    lines = []
    meter = CostMeter(sink=lines.append)
    Runner(scripted([call(cost=0.5), finish(cost=0.25)]), lambda c: ToolResult(True, ""), Budget(9, 9), hooks=[meter]).run()
    assert meter.usd == 0.75 and meter.tokens_in == 20 and meter.tokens_out == 10
    assert len(lines) == 2 and "$0.7500" in lines[-1]
