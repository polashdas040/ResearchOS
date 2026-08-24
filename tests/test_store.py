import os
import tempfile
from pathlib import Path

from backend.store import ThreadStore


def test_thread_store_persists_messages():
    descriptor, name = tempfile.mkstemp(
        dir=Path(__file__).resolve().parent.parent,
        suffix=".db",
    )
    os.close(descriptor)
    Path(name).unlink()
    try:
        path = Path(name)
        store = ThreadStore(path)
        store.append_message("guest", "user", "Hello")
        store.append_message("guest", "assistant", "Hi there")

        reloaded = ThreadStore(path)
        reloaded.load()

        thread = reloaded.get_thread("guest")
        assert [m.content for m in thread.messages] == ["Hello", "Hi there"]
    finally:
        Path(name).unlink(missing_ok=True)
