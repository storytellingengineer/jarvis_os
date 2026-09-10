# JARVIS OS

A personal AI operating system built incrementally as a real software project.

## Current milestone: v0.6.0 — FastAPI Service

JARVIS now exposes the same orchestrator used by the CLI through a lightweight HTTP API. The service keeps the existing conversation history and tool-calling architecture behind a stable `/chat` endpoint.

```text
Client
  ↓
FastAPI
  ↓
Orchestrator
  ├── Conversation History
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
- [ ] Web research
- [ ] Personal knowledge/RAG
- [ ] Voice interface
- [ ] Agent workflows
- [x] FastAPI service
- [ ] Deployment
- [ ] Desktop/web UI
- [ ] Observability and evaluations
- [ ] Permission and safety layer

## Security

Secrets are stored locally in `.env` and must never be committed to Git.
