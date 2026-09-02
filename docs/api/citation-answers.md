# Citation Answers

Citation-first answers are generated from `EvidencePack` records.

## Scope

`CitationFirstAnswerComposer` creates structured claims and citation IDs from evidence items. Validation rejects unknown citation IDs and claims whose text is not supported by the cited evidence.

When no evidence exists, the composer returns an evidence-unavailable response instead of inventing support.
