# PLAN 15 Evidence and Claim Graph

PLAN 15 introduces the first scientific reasoning graph layer.

## Decisions

- PostgreSQL stores graph records through `claims`, `evidence`, and `claim_evidence_links`.
- The repository enforces organization scope on reads and links.
- Claim records keep supporting and contradicting evidence as relationship edges, not embedded prose.
- Provenance traversal returns structured domain models for downstream verification.

Neo4j or another graph database is intentionally deferred.
