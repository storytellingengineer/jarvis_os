# JARVIS OS

A personal AI operating system built incrementally as a real software project.

## Current milestone: v0.4.0 — Tool Registry & Function Calling

JARVIS provides an interactive CLI backed by an LLM provider abstraction, an OpenAI implementation, in-memory conversation history, and a tool registry with real function calling.

```text
User
  ↓
CLI
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

Run JARVIS:

```bash
python -m app.main
```

Or, after installing the package:

```bash
jarvis
```

Try:

```text
You: Calculate (25 * 4) + 10
JARVIS: 110
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
- [x] Tool registry and function calling
- [x] Calculator tool
- [ ] Persistent memory
- [ ] Web research
- [ ] Personal knowledge/RAG
- [ ] Voice interface
- [ ] Agent workflows
- [ ] FastAPI service
- [ ] Deployment
- [ ] Desktop/web UI
- [ ] Observability and evaluations
- [ ] Permission and safety layer

## Security

Secrets are stored locally in `.env` and must never be committed to Git.
