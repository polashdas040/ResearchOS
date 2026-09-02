# Hybrid Retrieval

Hybrid retrieval combines dense vector search, lexical term matching, and metadata-scoped filtering.

## Scope

All retrieval calls require organization and project identifiers. Dense and lexical candidates are ranked separately, then merged with reciprocal rank fusion.

PLAN 12 returns retrieval candidates only. Reranking and EvidencePack construction begin in PLAN 13.
