# JARVIS OS

A personal AI operating system built incrementally as a real software project.

## Current milestone: v0.9.0 — Persistent API Memory

JARVIS now exposes its orchestrator through a FastAPI service and persists conversation history in SQLite. The CLI and API use the same memory abstraction, so local conversations survive process restarts.

```text
Client
  ↓
FastAPI
  ↓
Orchestrator
  ├── Persistent Conversation History
  └── Tool Registry
        ↓
     OpenAI Responses API
        ↓
   Tool Call → Execute → Result
        ↓
     JARVIS response
```

## API

Health check:

```text
GET /health
```

Chat:

```text
POST /chat
Content-Type: application/json

{"message": "Calculate (25 * 4) + 10"}
```

Response:

```json
{"response": "110"}
```

Clear local conversation memory:

```text
DELETE /memory
```

## Built-in tools

### Calculator

JARVIS can invoke a safe arithmetic calculator through the LLM tool-calling interface. The calculator parses arithmetic expressions rather than executing arbitrary Python code.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

Create `.env` from `.env.example` and add your OpenAI API key.

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.6-luna
LLM_API_KEY=your_api_key_here
JARVIS_MEMORY_PATH=data/jarvis.db
```

Run the CLI:

```bash
python -m app.main
```

Or run the API:

```bash
uvicorn app.api:app --reload
```

The interactive API documentation is then available at `/docs`.

## Development

Run tests with:

```bash
pytest
```

## Roadmap

- [x] Project foundation
- [x] LLM provider abstraction
- [x] OpenAI integration
- [x] Interactive CLI
- [x] Basic unit test
- [x] In-memory conversation history
- [x] Tool registry and function calling
- [x] Calculator tool
- [x] Persistent memory
- [x] FastAPI service
- [x] Web interface
- [x] Persistent memory for API
- [ ] Web research
- [ ] Personal knowledge/RAG
- [ ] Voice interface
- [ ] Agent workflows
- [ ] Observability and evaluations
- [ ] Permission and safety layer
- [ ] Production deployment hardening

## Security

Secrets are stored locally in `.env` and must never be committed to Git. The `/memory` endpoint is intended for the private personal deployment and should be protected before exposing JARVIS publicly.
