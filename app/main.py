"""JARVIS OS command-line entry point."""

from app.config import settings
from app.core.orchestrator import Orchestrator
from app.core.tools import Tool, ToolRegistry
from app.llm.openai_provider import OpenAIProvider
from app.tools.calculator import calculate


def build_tools() -> ToolRegistry:
    """Build the default JARVIS toolset."""
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="calculator",
            description="Evaluate a basic arithmetic expression.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A basic arithmetic expression such as (25 * 4) + 10.",
                    }
                },
                "required": ["expression"],
                "additionalProperties": False,
            },
            function=calculate,
        )
    )
    return registry


def main() -> None:
    """Start the interactive JARVIS session."""
    try:
        llm = OpenAIProvider(settings)
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        return

    jarvis = Orchestrator(llm, tools=build_tools())

    print("JARVIS OS v0.4.0")
    print(f"Model: {settings.llm_model}")
    print("Tools: calculator")
    print("Type 'exit' or 'quit' to close.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJARVIS: Goodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("JARVIS: Goodbye.")
            break

        try:
            print(f"JARVIS: {jarvis.respond(user_input)}\n")
        except Exception as exc:  # noqa: BLE001 - CLI boundary
            print(f"JARVIS: I couldn't complete that request. {exc}\n")


if __name__ == "__main__":
    main()
