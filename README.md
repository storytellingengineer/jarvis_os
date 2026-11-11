# JARVIS OS

A personal AI operating system built incrementally as a real software project.

## Current milestone: v1.8.0 — Push-to-talk Voice

JARVIS now supports a complete push-to-talk voice turn in the web interface:

```text
Microphone recording
       ↓
OpenAI speech-to-text
       ↓
Existing JARVIS orchestrator + conversation memory + tools
       ↓
OpenAI text-to-speech
       ↓
MP3 playback in the browser
```

- Tap **Start voice**, speak, then tap **Stop & send**.
- The browser uploads an audio recording to `POST /voice/chat`.
- JARVIS transcribes the recording, processes the transcript through the existing orchestrator, and returns spoken MP3 audio.
- The transcript and answer are returned in URL-encoded response headers for display in the chat.
- Audio uploads are limited to 20 MB and must use an audio content type.
- Audio is processed through the configured OpenAI API; this interface does not persist recordings.
- Voice models and voice are configurable with `JARVIS_STT_MODEL`, `JARVIS_TTS_MODEL`, and `JARVIS_TTS_VOICE`.

This is push-to-talk, not always-on listening. Wake-word detection and streaming/low-latency realtime conversation remain future milestones.

## v1.7 Stateful Agent Runtime

The lifecycle layer lives in `app/core/runtime.py`.

- **SessionState** stores bounded session metadata and operational events.
- **JarvisRuntime** provides explicit `start`, `wake`, `sleep`, and `stop` lifecycle controls.
- Work is accepted only while the runtime is `ready`.
- Existing multi-agent routing remains the execution backend; the runtime does not duplicate agent logic.
- Proactive behavior is exposed as an explicit injected hook, keeping background behavior testable and side-effect boundaries clear.
- The runtime is provider-agnostic, so voice can sit above it without changing orchestration primitives.

## v1.6 Multi-Agent Foundation

The multi-agent primitives live in `app/core/multiagent.py`.

- **AgentContext** carries the task, selected route, artifacts, and execution events.
- **AgentResult** provides a consistent result contract and optional next-agent routing.
- **SupervisorAgent** performs transparent deterministic routing for knowledge, coding, research, and general requests.
- **SpecialistAgent** adapts a handler into a registered specialist agent.
- **VerifierAgent** validates specialist output.
- **MultiAgentRuntime** executes supervisor routing and invokes the matching specialist when one is registered.
- Unknown routes are handled safely without executing an unregistered agent.

This is still an orchestration foundation. Future milestones will replace simple routing rules with model-assisted planning, add dedicated Knowledge/Coding/Research/Execution agents, and connect verification, memory, approvals, voice, and observability across the workflow.

## v1.5 Agent Evaluation + Failure Recovery

The evaluation/recovery layer lives in `app/core/evaluation.py` and `app/core/agent.py`.

- **AgentEvaluator** checks deterministic execution properties: task, plan, and result presence.
- **EvaluationResult** exposes pass/fail, a normalized score, individual criteria, and a failure reason.
- **FailureClassifier** separates transient failures, policy violations, empty results, exhausted budgets, and terminal failures.
- **RecoveryPolicy** permits only bounded retries for transient and empty-result failures.
- Recovery resets the per-request tool budget before a retry and records recovery events in the existing structured trace.
- Policy violations and exhausted tool budgets are never automatically retried.
- Evaluation does not log prompts, tool arguments, tool results, or model chain-of-thought.

## v1.4 Agent Observability

The observability layer lives in `app/core/observability.py` and records bounded operational events for each request:

- unique trace ID
- operation and model metadata
- planning / execution / verification lifecycle
- tool start, completion, failure, and latency
- tool-call counts
- response size
- request duration and final status
- recovery decisions and attempts
- evaluation score

Traces are emitted as JSON through the `jarvis.observability` logger. Tool arguments, user prompts, tool results, API keys, and model chain-of-thought are intentionally not logged.

## v1.3 Agent Runtime

The runtime is implemented in `app/core/agent.py` and models each task as a state machine:

- **Planner** creates a concise action plan before execution.
- **Executor** uses the existing LLM tool-calling loop and `ToolExecutionPolicy`.
- **TaskState** records plan, status, execution steps, errors, evaluation score, and recovery attempts.
- **Verifier** rejects empty or otherwise structurally invalid results and marks successful runs as verified.
- **Execution budget** remains bounded by the existing per-request tool-call policy.

## Roadmap

- [x] Project foundation
- [x] LLM provider abstraction
- [x] OpenAI integration
- [x] Interactive CLI
- [x] Conversation history
- [x] Tool registry and function calling
- [x] Calculator tool
- [x] Persistent memory
- [x] FastAPI service
- [x] Web interface
- [x] Tool execution policy
- [x] Native web research
- [x] Local personal knowledge retrieval
- [x] Document chunking
- [x] Semantic/vector retrieval
- [x] Hybrid keyword + semantic retrieval
- [x] Source/chunk citations
- [x] Agent runtime foundation
- [x] Planner / executor / verifier state flow
- [x] Bounded execution budget
- [x] Structured agent observability
- [x] Deterministic agent evaluation
- [x] Bounded agent failure recovery
- [x] Multi-agent context and agent contract foundation
- [x] Deterministic supervisor routing
- [x] Stateful runtime lifecycle
- [x] Push-to-talk voice interface (speech-to-text → JARVIS → text-to-speech)
- [ ] Model-assisted supervisor planning
- [ ] Dedicated Knowledge, Coding, Research, and Execution agents
- [ ] Agent-to-agent handoffs and shared memory
- [ ] Cross-agent verification and evaluation
- [ ] PDF/DOCX ingestion
- [ ] Retrieval evaluation suite
- [ ] Memory 2.0
- [ ] Wake-word integration
- [ ] Realtime streaming voice interface
- [ ] Computer / browser control
- [ ] Production deployment hardening

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
pip install -r requirements.txt
pip install -e .
```

Create `.env` from `.env.example` and set `LLM_API_KEY`.

Voice defaults are set in `.env.example`; override them in your local `.env` if needed.

Run the main CLI:

```bash
python -m app.main
```

Run the agent CLI:

```bash
python -m app.agent_cli
```

Or run the API:

```bash
uvicorn app.api:app --reload
```

Open `http://127.0.0.1:8000`, allow microphone access, and use **Start voice** / **Stop & send**.

Run tests with:

```bash
pytest
```

## Security

Secrets stay in local `.env` and must never be committed. The `/memory` endpoint is intended for a private deployment and should be protected before public exposure. Custom tools are guarded by an allowlist and per-request execution budget. Observability records operational metadata only and intentionally excludes prompts, tool arguments, tool results, and secrets.
