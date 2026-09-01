# PLAN 09 Figure Intelligence

PLAN 09 adds structured scientific figure understanding.

## Design

- `FigureExtractor` links persisted `FIGURE` document elements to image bytes, caption, page, and section metadata.
- `FigureIntelligenceService` depends on a `FigureVisionModel` protocol.
- `DeterministicFigureVisionModel` is the initial local adapter used for tests and development.
- `figures` stores caption linkage, image fingerprint, figure type, labels, components, relationships, axes, trends, architecture nodes, medical anatomy, confidence, and source page.

## Current Limits

This phase does not call an external VLM. A production VLM adapter can replace the deterministic adapter behind the same protocol.
