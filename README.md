# JARVIS OS

A personal AI operating system built incrementally as a real software project.

## Current milestone: v1.6.0 — Multi-Agent Orchestration Foundation

JARVIS combines persistent memory, guarded tools, native web search, hybrid local RAG, and an evolving planner/executor/verifier runtime. The v1.6 milestone introduces a composable multi-agent foundation: a supervisor routes requests to specialist agents, while shared context carries routes, artifacts, and operational events.

```text
User Task
   ↓
Supervisor / Router
   ↓
   ├── Knowledge Agent → Local RAG
   ├── Coding Agent → Code / Tests
   ├── Research Agent → Web / Synthesis
   └── General Agent
   ↓
Verifier / Evaluation
   ↓
Verified Response + Observability
```

## v1.6 Multi-Agent Foundation

The multi-agent primitives live in `app/core/multiagent.py`.

- **AgentContext** carries the task, selected route, artifacts, and execution events.
- **AgentResult** provides a consistent result contract and optional next-agent routing.
- **SupervisorAgent** performs transparent deterministic routing for knowledge, coding, research, and general requests.
- **SpecialistAgent** adapts a handler into a registered specialist agent.
- **MultiAgentRuntime** executes supervisor routing and invokes the matching specialist when one is registered.
- Unknown routes are handled safely without executing an unregistered agent.

This is the orchestration foundation, not the final autonomous system. Future milestones will replace simple routing rules with model-assisted planning, add dedicated Knowledge/Coding/Research/Execution agents, and connect verification, memory, approvals, and observability across the workflow.

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

A developer CLI is available for exercising the runtime directly:

```bash
python -m app.agent_cli
```

The main conversational CLI continues to use the stable orchestration path while the agent runtime remains separately testable.

## v1.2 RAG

Imported UTF-8 text or Markdown is chunked, embedded with `text-embedding-3-small` by default, stored locally in SQLite, and retrieved through hybrid semantic + SQLite FTS5 keyword ranking. Results include source/chunk citations such as `[notes.md#chunk-2]`.

Import a document:

```bash
python -m app.knowledge_cli path/to/document.md
```

Configuration:

```text
JARVIS_KNOWLEDGE_PATH=data/knowledge.db
JARVIS_EMBEDDING_MODEL=text-embedding-3-small
JARVIS_RAG_CHUNK_SIZE=500
JARVIS_RAG_CHUNK_OVERLAP=75
```

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
pip install -r requirements.txt
pip install -e .
```

Create `.env` from `.env.example` and set `LLM_API_KEY`.

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

Run tests with:

```bash
pytest
```

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
- [ ] Model-assisted supervisor planning
- [ ] Dedicated Knowledge, Coding, Research, and Execution agents
- [ ] Agent-to-agent handoffs and shared memory
- [ ] Cross-agent verification and evaluation
- [ ] PDF/DOCX ingestion
- [ ] Retrieval evaluation suite
- [ ] Memory 2.0
- [ ] Voice interface
- [ ] Production deployment hardening

## Security

Secrets stay in local `.env` and must never be committed. The `/memory` endpoint is intended for a private deployment and should be protected before public exposure. Custom tools are guarded by an allowlist and per-request execution budget. Observability records operational metadata only and intentionally excludes prompts, tool arguments, tool results, and secrets.
