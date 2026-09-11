"""HTTP API and web interface for JARVIS."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.core.orchestrator import Orchestrator
from app.core.tools import Tool, ToolRegistry
from app.llm.openai_provider import OpenAIProvider
from app.tools.calculator import calculate

app = FastAPI(title="JARVIS OS", version="0.8.0")
STATIC_INDEX = Path(__file__).resolve().parent.parent / "static" / "index.html"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)


class ChatResponse(BaseModel):
    response: str


@dataclass
class JarvisRuntime:
    orchestrator: Orchestrator


def build_tools() -> ToolRegistry:
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


def build_runtime() -> JarvisRuntime:
    try:
        llm = OpenAIProvider(settings)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    return JarvisRuntime(Orchestrator(llm, tools=build_tools()))


runtime: JarvisRuntime | None = None


def get_runtime() -> JarvisRuntime:
    global runtime
    if runtime is None:
        try:
            runtime = build_runtime()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return runtime


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_INDEX)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "jarvis-os", "version": "0.8.0"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    jarvis = get_runtime()
    try:
        return ChatResponse(response=jarvis.orchestrator.respond(request.message))
    except Exception as exc:  # noqa: BLE001 - API boundary
        raise HTTPException(status_code=500, detail="JARVIS could not process the request.") from exc
