# JARVIS OS

A personal AI operating system built incrementally as a real software project.

## Current milestone: v1.2.0 — Real RAG

JARVIS combines a FastAPI service, persistent SQLite conversation memory, guarded custom tools, native OpenAI web search, and a local RAG pipeline. Imported text/Markdown is chunked, embedded, stored locally in SQLite, and retrieved through hybrid semantic + keyword search with source citations.

```text
Client
  ↓
FastAPI / CLI
  ↓
Orchestrator
  ├── Persistent Conversation History
  ├── Tool Registry + Execution Policy
  ├── Hybrid Local RAG
  │     ├── Chunking
  │     ├── OpenAI Embeddings
  │     ├── Semantic Retrieval
  │     └── SQLite FTS5 Keyword Retrieval
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
JARVIS imports UTF-8 text or Markdown files into a local SQLite RAG index. Documents are split into overlapping chunks, embedded with `text-embedding-3-small` by default, and retrieved using hybrid semantic + keyword ranking. Results include source and chunk citations such as `[notes.md#chunk-2]`.

Import a document:

```bash
python -m app.knowledge_cli path/to/document.md
```

RAG configuration:

```text
JARVIS_KNOWLEDGE_PATH=data/knowledge.db
JARVIS_EMBEDDING_MODEL=text-embedding-3-small
JARVIS_RAG_CHUNK_SIZE=500
JARVIS_RAG_CHUNK_OVERLAP=75
```

The current implementation intentionally keeps the vector layer local and dependency-light: embeddings are stored in SQLite and cosine similarity is computed in-process. This is appropriate for a personal corpus and gives JARVIS a clean path toward a dedicated vector index later.

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
JARVIS_EMBEDDING_MODEL=text-embedding-3-small
JARVIS_RAG_CHUNK_SIZE=500
JARVIS_RAG_CHUNK_OVERLAP=75
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
- [x] Document chunking
- [x] Semantic/vector retrieval
- [x] Hybrid keyword + semantic retrieval
- [x] Source/chunk citations
- [ ] PDF/DOCX ingestion
- [ ] Retrieval evaluation suite
- [ ] Agent workflows
- [ ] Observability and evaluations
- [ ] Voice interface
- [ ] Production deployment hardening

## Security

Secrets stay in local `.env` and must never be committed. The `/memory` endpoint is intended for a private deployment and should be protected before public exposure. Custom tools are guarded by an allowlist and per-request execution budget.
