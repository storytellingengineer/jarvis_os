"""Structured, privacy-conscious observability for JARVIS execution."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger("jarvis.observability")


@dataclass
class Trace:
    """Execution trace containing operational events, not model chain-of-thought."""

    trace_id: str
    started_at: float = field(default_factory=time.time)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "running"
    error: str | None = None

    def event(self, name: str, **data: Any) -> None:
        """Record and emit one structured execution event."""
        event = {
            "trace_id": self.trace_id,
            "event": name,
            "timestamp": time.time(),
            **data,
        }
        self.events.append(event)
        logger.info(json.dumps(event, default=str, separators=(",", ":")))

    def finish(self, status: str = "completed", error: str | None = None) -> None:
        self.status = status
        self.error = error
        self.event(
            "request_finished",
            status=status,
            duration_ms=round((time.time() - self.started_at) * 1000, 2),
            error=error,
        )


class Observability:
    """Create bounded-scope traces for one JARVIS request at a time."""

    def start(self, operation: str, **data: Any) -> Trace:
        trace = Trace(trace_id=uuid.uuid4().hex)
        trace.event("request_started", operation=operation, **data)
        return trace


observability = Observability()
