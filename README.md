# JARVIS OS

A personal AI operating system built incrementally as a real software project.

## Current milestone: v1.1.0 — Personal Knowledge

JARVIS combines a FastAPI service, persistent SQLite conversation memory, guarded custom tools, native OpenAI web search, and a local SQLite FTS5 knowledge base. Local documents can be imported and retrieved through the same tool-calling loop.

```text
Client
  ↓
FastAPI / CLI
  ↓
Orchestrator
  ├── Persistent Conversation History
  ├── Tool Registry + Execution Policy
  ├── Local Knowledge Search
  └── Web Search
        ↓
   OpenAI Responses API
```

## Capabilities

### Calculator
Safe arithmetic evaluation through an LLM function tool.

### Web Research
Native OpenAI web search for current, recent, or time-sensitive questions. Disable with `JARVIS_WEB_SEARCH=false`.

### Personal Knowledge / RAG
JARVIS can search imported UTF-8 text or Markdown files using SQLite FTS5. This keeps the first RAG layer local and dependency-light.

Import a document:

```bash
python -m app.knowledge_cli path/to/document.md
```

The default knowledge database is `data/knowledge.db`; override it with `JARVIS_KNOWLEDGE_PATH`.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
pip install -r requirements.txt
pip install -e .
```

Create `.env` from `.env.example`:

```text
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.6-luna
LLM_API_KEY=your_api_key_here
JARVIS_MEMORY_PATH=data/jarvis.db
JARVIS_KNOWLEDGE_PATH=data/knowledge.db
JARVIS_WEB_SEARCH=true
```

Run the CLI:

```bash
python -m app.main
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
- [x] Basic unit test
- [x] Conversation history
- [x] Tool registry and function calling
- [x] Calculator tool
- [x] Persistent memory
- [x] FastAPI service
- [x] Web interface
- [x] Tool execution policy
- [x] Native web research
- [x] Local personal knowledge retrieval
- [ ] Semantic/vector retrieval
- [ ] Voice interface
- [ ] Agent workflows
- [ ] Observability and evaluations
- [ ] Production deployment hardening

## Security

Secrets stay in local `.env` and must never be committed. The `/memory` endpoint is intended for a private deployment and should be protected before public exposure. Custom tools are guarded by an allowlist and per-request execution budget.
