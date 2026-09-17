# JARVIS OS — v2.0 Implementation Track

## Objective

Turn the current planner/executor/verifier prototype into a testable, resilient personal AI operating system without sacrificing bounded execution, privacy, or local control.

## Milestones

### v1.6 — Knowledge ingestion
- PDF and DOCX extraction behind optional dependencies
- Source metadata and stable document IDs
- Ingestion errors reported without partial silent writes

### v1.7 — Retrieval quality
- Golden query dataset
- Recall@k, MRR, and citation coverage metrics
- Regression tests for hybrid retrieval

### v1.8 — Agent reliability
- Explicit task deadlines
- Retry backoff hooks
- Idempotency keys for tool execution
- Structured failure taxonomy

### v1.9 — Memory 2.0
- Memory types: fact, preference, event, task
- Confidence and source metadata
- User-controlled deletion and export
- No automatic persistence of secrets or sensitive payloads

### v2.0 — Production-ready local agent core
- Versioned runtime configuration
- Health/readiness diagnostics
- Evaluation and trace correlation
- Safe tool approval mode for side-effecting actions
- CLI smoke-test command
- Documentation for local deployment and rollback

## Non-negotiable engineering constraints

1. Keep tool execution allowlisted and budgeted.
2. Never log prompts, tool arguments, tool results, secrets, or chain-of-thought.
3. Retries must be bounded and restricted to explicitly recoverable failures.
4. All new capabilities require deterministic tests.
5. Preserve backwards compatibility for the main CLI and API.
