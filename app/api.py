"""HTTP API and web interface for JARVIS OS."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.core.history import ConversationHistory
from app.core.memory import PersistentMemory
from app.core.multiagent import MultiAgentRuntime, SpecialistAgent, VerifierAgent
from app.core.orchestrator import Orchestrator
from app.core.runtime import JarvisRuntime as StatefulJarvisRuntime
from app.core.runtime import RuntimeState
from app.core.tools import Tool, ToolRegistry
from app.llm.openai_provider import OpenAIProvider
from app.tools.calculator import calculate
from app.tools.knowledge import search_knowledge

app = FastAPI(title="JARVIS OS", version="0.7.0")
STATIC_INDEX = Path(__file__).resolve().parent.parent / "static" / "index.html"
MEMORY_PATH = Path(settings.memory_path)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)


class ChatResponse(BaseModel):
    response: str


class RuntimeStatus(BaseModel):
    session_id: str
    state: str
    turn_count: int
    last_task: str
    last_result: str
    events: list[str]


@dataclass
class JarvisService:
    """Application services wired to one stateful assistant session."""

    orchestrator: Orchestrator
    memory: PersistentMemory
    lifecycle: StatefulJarvisRuntime


def build_tools() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="calculator",
            description="Evaluate a basic arithmetic expression.",
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
            function=calculate,
        )
    )
    registry.register(
        Tool(
            name="search_knowledge",
            description=(
                "Search the user's local personal knowledge base for information "
                "from imported documents using semantic and keyword retrieval."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            function=search_knowledge,
        )
    )
    return registry


def build_runtime() -> JarvisService:
    """Build the real chat engine and connect it to the lifecycle runtime."""
    try:
        llm = OpenAIProvider(settings)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    memory = PersistentMemory(MEMORY_PATH)
    history = ConversationHistory(store=memory)
    orchestrator = Orchestrator(llm, history=history, tools=build_tools())

    # Every specialist delegates to the existing guarded orchestrator for now.
    # This integrates lifecycle and routing without pretending placeholder
    # specialist implementations are already autonomous agents.
    specialists = {
        name: SpecialistAgent(
            name,
            lambda context: orchestrator.respond(context.task),
        )
        for name in ("knowledge", "coding", "research", "general")
    }
    agent_runtime = MultiAgentRuntime(
        specialists,
        verifier=VerifierAgent(),
    )
    lifecycle = StatefulJarvisRuntime(agent_runtime, session_id="desktop")
    lifecycle.start()
    return JarvisService(
        orchestrator=orchestrator,
        memory=memory,
        lifecycle=lifecycle,
    )


runtime: JarvisService | None = None


def get_runtime() -> JarvisService:
    global runtime
    if runtime is None:
        try:
            runtime = build_runtime()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return runtime


def runtime_status(jarvis: JarvisService) -> RuntimeStatus:
    session = jarvis.lifecycle.session
    return RuntimeStatus(
        session_id=session.session_id,
        state=session.state.value,
        turn_count=session.turn_count,
        last_task=session.last_task,
        last_result=session.last_result,
        events=list(session.events[-50:]),
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_INDEX)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "jarvis-os", "version": "0.7.0"}


@app.get("/runtime", response_model=RuntimeStatus)
def get_runtime_status() -> RuntimeStatus:
    """Inspect the active JARVIS session and lifecycle state."""
    return runtime_status(get_runtime())


@app.post("/runtime/wake", response_model=RuntimeStatus)
def wake_runtime() -> RuntimeStatus:
    return runtime_status_after(get_runtime().lifecycle.wake())


@app.post("/runtime/sleep", response_model=RuntimeStatus)
def sleep_runtime() -> RuntimeStatus:
    return runtime_status_after(get_runtime().lifecycle.sleep())


@app.post("/runtime/stop", response_model=RuntimeStatus)
def stop_runtime() -> RuntimeStatus:
    return runtime_status_after(get_runtime().lifecycle.stop())


def runtime_status_after(session) -> RuntimeStatus:
    """Build a status response after a lifecycle transition."""
    return RuntimeStatus(
        session_id=session.session_id,
        state=session.state.value,
        turn_count=session.turn_count,
        last_task=session.last_task,
        last_result=session.last_result,
        events=list(session.events[-50:]),
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    jarvis = get_runtime()
    if jarvis.lifecycle.session.state is not RuntimeState.READY:
        raise HTTPException(
            status_code=409,
            detail=f"JARVIS runtime is {jarvis.lifecycle.session.state.value}",
        )
    try:
        session = jarvis.lifecycle.run(request.message)
        if not session.last_result:
            raise RuntimeError("No specialist result was produced")
        return ChatResponse(response=session.last_result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="JARVIS could not process the request.",
        ) from exc


@app.delete("/memory", status_code=204)
def clear_memory() -> None:
    get_runtime().orchestrator.clear_history()
