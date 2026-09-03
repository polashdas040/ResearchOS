# Evidence Graph

The evidence graph stores claims, evidence records, and support or contradiction relationships.

## Scope

Claims and evidence are tenant scoped by organization. A claim can link to supporting evidence and contradicting evidence. Provenance traversal returns the claim plus the linked evidence records needed to inspect its support.

This phase does not add public HTTP routes for graph editing.
