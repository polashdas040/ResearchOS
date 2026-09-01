# PLAN 07 Scientific Document Intelligence

PLAN 07 adds the first structured scientific document ingestion layer.

## Design

- Uploaded files remain binary objects plus PostgreSQL file metadata.
- `ScientificPdfParser` converts PDF bytes into `StructuredDocument`.
- `documents` stores one parsed document per source file.
- `document_elements` stores ordered scientific elements with page, section, caption, and bounding-box fields.
- `DocumentParseJobHandler` runs parsing from the worker side, not inside HTTP routes.

## Element Types

The initial schema supports `TITLE`, `ABSTRACT`, `HEADING`, `PARAGRAPH`, `TABLE`, `FIGURE`, `EQUATION`, `REFERENCE`, and `CAPTION`.

## Current Limits

The parser is a deterministic initial adapter for structured text extracted from PDFs. A full Docling-backed parser can replace this adapter behind the same schema without changing storage or worker boundaries.
