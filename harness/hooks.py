from __future__ import annotations

from harness.types import Action, RunState, Step, ToolCall, ToolResult


class Hook:
    """Subclass and override what you need. Hooks must not mutate state except via state.emit()."""

    def on_step(self, state: RunState, step: Step) -> Action | None:
        return None

    def on_tool_call(self, state: RunState, call: ToolCall) -> ToolCall | ToolResult | None:
        """Return a ToolCall to replace the call, a ToolResult to skip the tool entirely."""
        return None

    def on_tool_result(self, state: RunState, call: ToolCall, result: ToolResult) -> ToolResult | None:
        """Return a ToolResult to replace the result."""
        return None
