import tempfile
from pathlib import Path

from backend.memory import MemoryIndex


def test_memory_index_returns_relevant_chunk():
    with tempfile.TemporaryDirectory() as temp_dir:
        index = MemoryIndex(Path(temp_dir))
        try:
            index.add_texts(
                thread_id="guest",
                texts=[
                    "LLM agents use planning and tools.",
                    "Bananas are yellow.",
                ],
            )

            hits = index.search("How do LLM agents use tools?", thread_id="guest", k=1)
        finally:
            index.close()

    assert hits[0].text == "LLM agents use planning and tools."
