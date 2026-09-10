from app.core.tools import Tool, ToolRegistry
from app.tools.calculator import calculate


def test_calculator_handles_basic_arithmetic() -> None:
    assert calculate("(25 * 4) + 10") == 110


def test_calculator_rejects_python_execution() -> None:
    try:
        calculate("__import__('os').system('echo unsafe')")
    except (ValueError, SyntaxError):
        pass
    else:
        raise AssertionError("Unsafe expression was executed")


def test_registry_registers_and_executes_tools() -> None:
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="calculator",
            description="Calculate arithmetic.",
            parameters={"type": "object"},
            function=calculate,
        )
    )

    assert registry.execute("calculator", {"expression": "10 + 5"}) == 15
    assert registry.schemas()[0]["name"] == "calculator"


def test_registry_rejects_duplicate_tools() -> None:
    registry = ToolRegistry()
    tool = Tool("demo", "Demo tool", {"type": "object"}, lambda: "ok")
    registry.register(tool)

    try:
        registry.register(tool)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate tool registration was accepted")
