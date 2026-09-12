import pytest

from app.core.policy import ToolExecutionPolicy
from app.core.tools import Tool, ToolRegistry


def make_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="echo",
            description="Echo text",
            parameters={"type": "object", "properties": {}},
            function=lambda: "ok",
        )
    )
    registry.register(
        Tool(
            name="other",
            description="Another tool",
            parameters={"type": "object", "properties": {}},
            function=lambda: "other",
        )
    )
    return registry


def test_policy_allows_registered_tool() -> None:
    policy = ToolExecutionPolicy(allowed_tools={"echo"})
    assert policy.execute(make_registry(), "echo", {}) == "ok"
    assert policy.calls_used == 1


def test_policy_rejects_disallowed_tool() -> None:
    policy = ToolExecutionPolicy(allowed_tools={"echo"})
    with pytest.raises(PermissionError, match="not allowed"):
        policy.execute(make_registry(), "other", {})


def test_policy_bounds_tool_calls() -> None:
    policy = ToolExecutionPolicy(max_tool_calls=1)
    registry = make_registry()
    assert policy.execute(registry, "echo", {}) == "ok"
    with pytest.raises(RuntimeError, match="Maximum tool calls exceeded"):
        policy.execute(registry, "echo", {})
