"""Tests for the stateful JARVIS runtime."""

import pytest

from app.core.multiagent import build_demo_runtime
from app.core.runtime import JarvisRuntime, RuntimeState


def test_runtime_wake_run_and_sleep() -> None:
    runtime = JarvisRuntime(build_demo_runtime(), session_id="test")

    assert runtime.session.state is RuntimeState.SLEEPING
    runtime.start()
    assert runtime.session.state is RuntimeState.READY

    state = runtime.run("research the latest AI evaluation approaches")
    assert state.state is RuntimeState.READY
    assert state.turn_count == 1
    assert state.last_task.startswith("research")
    assert "runtime:turn_completed" in state.events
    assert "supervisor:routed:research" in state.events

    runtime.sleep()
    assert runtime.session.state is RuntimeState.SLEEPING

    with pytest.raises(RuntimeError, match="Runtime is sleeping"):
        runtime.run("run another task")


def test_runtime_rejects_empty_tasks() -> None:
    runtime = JarvisRuntime(build_demo_runtime())
    runtime.start()

    with pytest.raises(ValueError, match="Task must not be empty"):
        runtime.run("   ")


def test_proactive_hook_is_explicit_and_bounded() -> None:
    calls = []

    def hook(session):
        calls.append(session.turn_count)
        return "check-in"

    runtime = JarvisRuntime(
        build_demo_runtime(),
        proactive_hook=hook,
    )

    assert runtime.proactive_check() is None

    runtime.start()
    assert runtime.proactive_check() == "check-in"
    assert calls == [0]
    assert "runtime:proactive_signal" in runtime.session.events


def test_stop_preserves_session_metadata() -> None:
    runtime = JarvisRuntime(build_demo_runtime(), session_id="persistent")
    runtime.start()
    runtime.run("write a simple test plan")
    runtime.stop()

    assert runtime.session.state is RuntimeState.STOPPED
    assert runtime.session.turn_count == 1

    runtime.wake()
    assert runtime.session.state is RuntimeState.READY
    assert runtime.session.turn_count == 1
