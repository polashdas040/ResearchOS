from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import chromadb


@dataclass
class MemoryHit:
    text: str
    metadata: dict[str, str]
    score: float | None = None


class _DeterministicEmbedding:
    dimensions = 256
    token_pattern = re.compile(r"[a-z0-9]+")

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def name(self) -> str:
        return "deterministic-local"

    @classmethod
    def _embed(cls, text: str) -> list[float]:
        vector = [0.0] * cls.dimensions
        for token in cls.token_pattern.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
            vector[int.from_bytes(digest, "big") % cls.dimensions] += 1.0
        length = math.sqrt(sum(value * value for value in vector))
        return [value / length for value in vector] if length else vector


class MemoryIndex:
    def __init__(self, persist_dir):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(
            name="memory",
            embedding_function=_DeterministicEmbedding(),
        )

    def add_texts(self, thread_id: str, texts: list[str]) -> None:
        if not texts:
            return
        self._collection.add(
            ids=[str(uuid4()) for _ in texts],
            documents=texts,
            metadatas=[{"thread_id": thread_id} for _ in texts],
        )

    def search(self, query: str, thread_id: str, k: int = 3) -> list[MemoryHit]:
        if k <= 0:
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=k,
            where={"thread_id": thread_id},
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return [
            MemoryHit(
                text=text,
                metadata=metadata,
                score=1.0 - distance if distance is not None else None,
            )
            for text, metadata, distance in zip(documents, metadatas, distances)
        ]
