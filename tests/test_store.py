from backend.store import ThreadStore


def test_thread_store_persists_messages(tmp_path):
    path = tmp_path / "threads.json"
    store = ThreadStore(path)
    store.append_message("guest", "user", "Hello")
    store.append_message("guest", "assistant", "Hi there")

    reloaded = ThreadStore(path)
    reloaded.load()

    thread = reloaded.get_thread("guest")
    assert [m.content for m in thread.messages] == ["Hello", "Hi there"]
