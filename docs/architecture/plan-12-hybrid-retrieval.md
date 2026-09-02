# PLAN 12 Hybrid Scientific Retrieval

PLAN 12 adds retrieval composition over semantic chunks.

## Decisions

- `DenseRetriever` delegates to the `VectorStore` interface from PLAN 11.
- `LexicalRetriever` performs deterministic exact-term ranking over scoped semantic chunks.
- `HybridRetriever` combines dense and lexical rankings with reciprocal rank fusion.
- Tenant and project filters are applied before ranking in both retrieval paths.

This phase does not add reranking, evidence packs, citation validation, or answer generation.
