from __future__ import annotations

import sys

from harness.hooks import Hook


class CostMeter(Hook):
    """Running totals, one line per step to sink (default stderr). Budget enforcement lives in Runner."""

    def __init__(self, sink=None):
        self.sink = sink or (lambda s: print(s, file=sys.stderr))
        self.usd = 0.0
        self.tokens_in = 0
        self.tokens_out = 0

    def on_step(self, state, step):
        self.usd += step.cost_usd
        self.tokens_in += step.tokens_in
        self.tokens_out += step.tokens_out
        self.sink(f"step {state.step} total ${self.usd:.4f} tokens {self.tokens_in}in/{self.tokens_out}out")
