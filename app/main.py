from app.config import settings
from app.core.history import ConversationHistory
from app.core.memory import PersistentMemory
from app.core.orchestrator import Orchestrator
from app.core.tools import Tool, ToolRegistry
from app.llm.openai_provider import OpenAIProvider
from app.tools.calculator import calculate
from app.tools.knowledge import search_knowledge


def build_tools() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(Tool(name="calculator", description="Evaluate a basic arithmetic expression.", parameters={"type":"object","properties":{"expression":{"type":"string"}},"required":["expression"],"additionalProperties":False}, function=calculate))
    registry.register(Tool(name="search_knowledge", description="Search the user's local personal knowledge base for information from imported documents using semantic and keyword retrieval.", parameters={"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer","minimum":1,"maximum":10}},"required":["query"],"additionalProperties":False}, function=search_knowledge))
    return registry


def main() -> None:
    try:
        llm = OpenAIProvider(settings)
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        return
    memory = PersistentMemory()
    history = ConversationHistory(store=memory)
    jarvis = Orchestrator(llm, history=history, tools=build_tools())
    print("JARVIS OS v1.2.0")
    print(f"Model: {settings.llm_model}")
    print("Memory: persistent (SQLite)")
    print("Tools: calculator + hybrid RAG + web search")
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
        except Exception as exc:
            print(f"JARVIS: I couldn't complete that request. {exc}\n")


if __name__ == "__main__":
    main()
