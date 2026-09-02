# PLAN 11 Vector Retrieval

PLAN 11 adds the vector store boundary for semantic retrieval.

## Design

- `VectorStore` is the provider protocol.
- `ChromaVectorStore` is the initial Chroma-compatible implementation.
- Vector documents are derived from semantic chunks.
- Every search is scoped by organization and project.
- Document deletion removes only vectors matching organization, project, and document.

## Current Limits

The initial implementation is in-process for deterministic local tests. A real ChromaDB client can replace it behind the same `VectorStore` protocol without changing callers.
