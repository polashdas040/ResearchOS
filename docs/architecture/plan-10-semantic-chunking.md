# PLAN 10 Semantic Chunking

PLAN 10 adds semantic document chunking for future retrieval.

## Design

- `SemanticChunker` creates chunks from structured document elements, not arbitrary token windows.
- Chunks preserve organization, project, document, source element, page, section, and chunk type.
- Tables stay together as table chunks.
- Figure captions stay with figure chunks.
- `semantic_chunks` stores retrievable chunk metadata in PostgreSQL.

## Current Limits

This phase does not embed chunks or write to ChromaDB. Vector persistence begins in PLAN 11.
