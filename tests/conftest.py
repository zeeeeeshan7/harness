from harness.types import Step, ToolCall


def scripted(steps):
    """step_fn that plays a fixed list, indexed by completed steps."""
    return lambda state: steps[state.step]


def call(name="t", cost=0.01, **args):
    return Step(ToolCall(name, args), None, cost, 10, 5)


def finish(answer="ok", cost=0.01):
    return Step(None, answer, cost, 10, 5)
