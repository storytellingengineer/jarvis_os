from app.core.observability import Observability


def test_trace_records_events_and_completion() -> None:
    observer = Observability()
    trace = observer.start("test.operation", model="test-model")

    trace.event("tool_started", tool="calculator")
    trace.finish("completed")

    assert trace.trace_id
    assert trace.status == "completed"
    assert [event["event"] for event in trace.events] == [
        "request_started",
        "tool_started",
        "request_finished",
    ]
    assert trace.events[0]["operation"] == "test.operation"
    assert trace.events[1]["tool"] == "calculator"
    assert "duration_ms" in trace.events[-1]


def test_trace_records_failure_without_logging_payloads() -> None:
    observer = Observability()
    trace = observer.start("test.operation", input_length=42)
    trace.finish("failed", "RuntimeError")

    assert trace.status == "failed"
    assert trace.error == "RuntimeError"
    assert trace.events[-1]["error"] == "RuntimeError"
    assert "input" not in trace.events[0]
    assert "api_key" not in trace.events[0]
