"""HTTP API and web interface for JARVIS."""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.config import settings
from app.core.history import ConversationHistory
from app.core.memory import PersistentMemory
from app.core.orchestrator import Orchestrator
from app.core.tools import Tool, ToolRegistry
from app.llm.openai_provider import OpenAIProvider
from app.tools.calculator import calculate
from app.tools.knowledge import search_knowledge

APP_VERSION = "0.8.0"
MAX_VOICE_UPLOAD_BYTES = 20 * 1024 * 1024

app = FastAPI(title="JARVIS OS", version=APP_VERSION)
STATIC_INDEX = Path(__file__).resolve().parent.parent / "static" / "index.html"
MEMORY_PATH = Path(settings.memory_path)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)


class ChatResponse(BaseModel):
    response: str


@dataclass
class JarvisRuntime:
    orchestrator: Orchestrator
    memory: PersistentMemory
    speech: OpenAIProvider


def build_tools() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(Tool(name="calculator", description="Evaluate a basic arithmetic expression.", parameters={"type":"object","properties":{"expression":{"type":"string"}},"required":["expression"],"additionalProperties":False}, function=calculate))
    registry.register(Tool(name="search_knowledge", description="Search the user's local personal knowledge base for information from imported documents using semantic and keyword retrieval.", parameters={"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer","minimum":1,"maximum":10}},"required":["query"],"additionalProperties":False}, function=search_knowledge))
    return registry


def build_runtime() -> JarvisRuntime:
    try:
        speech = OpenAIProvider(settings)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    memory = PersistentMemory(MEMORY_PATH)
    history = ConversationHistory(store=memory)
    return JarvisRuntime(
        orchestrator=Orchestrator(speech, history=history, tools=build_tools()),
        memory=memory,
        speech=speech,
    )


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
    return {"status": "ok", "service": "jarvis-os", "version": APP_VERSION}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    jarvis = get_runtime()
    try:
        return ChatResponse(response=jarvis.orchestrator.respond(request.message))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="JARVIS could not process the request.") from exc


@app.post("/voice/chat", responses={200: {"content": {"audio/mpeg": {}}}})
def voice_chat(audio: UploadFile = File(...)) -> Response:
    """Transcribe a voice turn, run it through JARVIS, and return spoken MP3 audio."""
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="Upload an audio recording.")
    audio_bytes = audio.file.read(MAX_VOICE_UPLOAD_BYTES + 1)
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="The audio recording is empty.")
    if len(audio_bytes) > MAX_VOICE_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Audio uploads must be 20 MB or smaller.")

    jarvis = get_runtime()
    try:
        transcript = jarvis.speech.transcribe_audio(
            audio_bytes,
            filename=audio.filename or "recording.webm",
            content_type=audio.content_type,
        ).strip()
        if not transcript:
            raise HTTPException(status_code=422, detail="No speech was detected. Try again.")
        answer = jarvis.orchestrator.respond(transcript)
        spoken_audio = jarvis.speech.synthesize_speech(answer)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="JARVIS voice processing failed. Check the API configuration and try again.",
        ) from exc

    return Response(
        content=spoken_audio,
        media_type="audio/mpeg",
        headers={
            "X-Jarvis-Transcript": quote(transcript, safe=""),
            "X-Jarvis-Response": quote(answer, safe=""),
            "Cache-Control": "no-store",
        },
    )


@app.delete("/memory", status_code=204)
def clear_memory() -> None:
    get_runtime().orchestrator.clear_history()
