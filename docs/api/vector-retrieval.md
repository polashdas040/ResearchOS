# Vector Retrieval

Vector retrieval stores semantic chunk embeddings behind a provider interface.

## Scope

Search requests must include organization and project identifiers. The vector store filters on both before ranking candidates.

ChromaDB is retrieval infrastructure only. PostgreSQL remains the authoritative source for application records and chunk metadata.
