# Semantic Chunks

Semantic chunks are retrieval-ready records derived from structured document elements.

## Metadata

Each chunk stores tenant, project, document, source element, page, section, element-derived chunk type, ordered sequence, and content.

Chunks are persisted in PostgreSQL. PLAN 11 will add tenant-scoped vector storage for semantic search.
