from backend.memory import MemoryIndex


def test_memory_index_returns_relevant_chunk(tmp_path):
    index = MemoryIndex(tmp_path / "chroma")
    index.add_texts(
        thread_id="guest",
        texts=[
            "LLM agents use planning and tools.",
            "Bananas are yellow.",
        ],
    )

    hits = index.search("How do LLM agents use tools?", thread_id="guest", k=1)
    assert hits[0].text == "LLM agents use planning and tools."
