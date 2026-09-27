# Multi-Agent Verification

JARVIS now supports an optional verification stage after a specialist agent runs.

## Flow

```text
Task
  -> SupervisorAgent
  -> SpecialistAgent
  -> Optional VerifierAgent
  -> AgentContext artifacts + events
```

## Usage

```python
from app.core.multiagent import MultiAgentRuntime, SpecialistAgent, VerifierAgent

runtime = MultiAgentRuntime(
    agents={
        "coding": SpecialistAgent("coding", lambda context: "implemented"),
    },
    verifier=VerifierAgent(),
)

context = runtime.run("Implement this function")
assert context.artifacts["verification"] == "approved"
```

The default verifier rejects empty output. A custom validator can be supplied for domain-specific checks. Verification is optional to preserve compatibility with the basic routing runtime.
