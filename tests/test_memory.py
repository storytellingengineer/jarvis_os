from pathlib import Path

from app.core.history import ConversationHistory
from app.core.memory import PersistentMemory


def test_memory_survives_new_history_instance(tmp_path: Path) -> None:
    database = tmp_path / "jarvis.db"
    memory = PersistentMemory(database)

    first = ConversationHistory(store=memory)
    first.add("User", "My project is JARVIS OS.")
    first.add("JARVIS", "Understood.")

    second = ConversationHistory(store=PersistentMemory(database))

    assert "User: My project is JARVIS OS." in second.as_prompt()
    assert "JARVIS: Understood." in second.as_prompt()


def test_clear_removes_persistent_memory(tmp_path: Path) -> None:
    database = tmp_path / "jarvis.db"
    first = ConversationHistory(store=PersistentMemory(database))
    first.add("User", "Temporary memory")
    first.clear()

    second = ConversationHistory(store=PersistentMemory(database))

    assert len(second) == 0
