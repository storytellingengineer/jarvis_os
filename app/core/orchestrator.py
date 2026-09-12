"""Central coordinator for JARVIS requests."""

from app.core.history import ConversationHistory
from app.core.policy import ToolExecutionPolicy
from app.core.tools import ToolRegistry
from app.llm.provider import LLMProvider


SYSTEM_PROMPT = """You are JARVIS, a personal AI operating system.
Be concise, accurate, and practical. When you are unsure, say so.
Use the conversation history to maintain context and answer follow-up questions naturally.
Use available tools when they are appropriate instead of doing tool work manually.
For current, recent, or time-sensitive information, use web search when available.
Never claim that a tool was executed unless the tool result was actually returned.
"""


class Orchestrator:
    """Route user input to the configured AI capability."""

    def __init__(
        self,
        llm: LLMProvider,
        history: ConversationHistory | None = None,
        tools: ToolRegistry | None = None,
        policy: ToolExecutionPolicy | None = None,
    ) -> None:
        self._llm = llm
        self._history = history or ConversationHistory()
        self._tools = tools or ToolRegistry()
        self._policy = policy or ToolExecutionPolicy()

    def respond(self, user_input: str) -> str:
        """Generate a response using conversation context and guarded tools."""
        self._policy.reset()
        self._history.add("User", user_input)
        prompt = f"{SYSTEM_PROMPT}\n\nConversation:\n{self._history.as_prompt()}\nJARVIS:"

        generate_with_tools = getattr(self._llm, "generate_with_tools", None)
        if generate_with_tools and len(self._tools):
            response = generate_with_tools(
                prompt,
                self._tools.schemas(),
                lambda name, arguments: self._policy.execute(
                    self._tools, name, arguments
                ),
            )
        else:
            response = self._llm.generate(prompt)

        self._history.add("JARVIS", response)
        return response

    def clear_history(self) -> None:
        """Clear the current session's conversation history."""
        self._history.clear()
