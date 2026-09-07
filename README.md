# JARVIS OS

A personal AI operating system built incrementally as a real software project.

## Current milestone: v0.3.0 — Conversation History

JARVIS provides an interactive CLI backed by an LLM provider abstraction, an OpenAI implementation, and in-memory conversation history for the current session.

```text
User
  ↓
CLI
  ↓
Orchestrator
  ↓
Conversation History
  ↓
LLM Provider
  ↓
OpenAI Responses API
  ↓
JARVIS response
  ↓
Conversation History
```

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

Run JARVIS:

```bash
python -m app.main
```

Or, after installing the package:

```bash
jarvis
```

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
- [ ] Tool registry and function calling
- [ ] Persistent memory
- [ ] Web research
- [ ] Personal knowledge/RAG
- [ ] Voice interface
- [ ] Agent workflows
- [ ] Desktop/web UI
- [ ] Observability and evaluations
- [ ] Permission and safety layer

## Security

Secrets are stored locally in `.env` and must never be committed to Git.
