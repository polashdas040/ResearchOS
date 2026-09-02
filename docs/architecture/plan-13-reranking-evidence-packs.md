# PLAN 13 Reranking and Evidence Packs

PLAN 13 adds the boundary between raw retrieval candidates and answer generation.

## Decisions

- `Reranker` is a protocol so later model-based rerankers can replace the deterministic initial adapter.
- `KeywordReranker` gives reproducible local ordering for tests and development.
- `EvidencePack` stores structured `EvidenceItem` records instead of prose retrieval summaries.
- Source metadata is copied from retrieval candidates so page and section provenance survive reranking.

This phase intentionally stops before citation validation and answer generation.
