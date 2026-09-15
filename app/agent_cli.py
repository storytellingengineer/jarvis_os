"""Developer entrypoint for exercising the v1.3 agent runtime."""

from app.config import settings
from app.core.agent import AgentRuntime
from app.core.policy import ToolExecutionPolicy
from app.core.tools import ToolRegistry
from app.llm.openai_provider import OpenAIProvider
from app.main import build_tools


def main() -> None:
    llm = OpenAIProvider(settings)
    tools: ToolRegistry = build_tools()
    policy = ToolExecutionPolicy(max_tool_calls=5)
    agent = AgentRuntime(llm, tools, policy)

    task = input("Task: ").strip()
    if not task:
        return

    state = agent.run(
        task,
        "You are JARVIS. Execute the user's task accurately and safely.",
        lambda name, arguments: policy.execute(tools, name, arguments),
    )
    print(f"\nJARVIS: {state.result}")
    print(f"Status: {state.status} | Steps: {' -> '.join(state.steps)} | Tool calls: {policy.calls_used}")


if __name__ == "__main__":
    main()
