# PLAN 14 Citation-First Answer Generation

PLAN 14 adds the first evidence-grounded answer boundary.

## Decisions

- Answers are represented by `CitationFirstAnswer`, not prose-only strings.
- Each `SupportedClaim` must carry citation IDs.
- Citation IDs are generated from real `EvidencePack` items.
- Validation rejects fake citation IDs and unsupported claim text.

This phase uses deterministic exact evidence text as the supported claim statement. Later phases can add model-generated paraphrasing only after stronger claim verification exists.
