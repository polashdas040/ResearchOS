# Evidence Packs

Evidence packs are serializable retrieval bundles prepared for downstream answer generation.

## Scope

`EvidencePackBuilder` accepts retrieval candidates, reranks them, limits the final set, and preserves source metadata including document ID, page, section, element type, retrieval score, and rerank score.

PLAN 13 does not generate final answers or validate citations. Citation-first answer generation begins in PLAN 14.
