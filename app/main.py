"""JARVIS OS command-line entry point."""

from app.config import settings
from app.core.orchestrator import Orchestrator
from app.llm.openai_provider import OpenAIProvider


def main() -> None:
    """Start the interactive JARVIS session."""
    try:
        llm = OpenAIProvider(settings)
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        return

    jarvis = Orchestrator(llm)

    print("JARVIS OS v0.2.0")
    print(f"Model: {settings.llm_model}")
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
