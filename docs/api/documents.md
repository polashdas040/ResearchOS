# Document Intelligence

Structured document intelligence is produced by the worker through `DOCUMENT_PARSE` jobs.

## Stored Data

- `documents`: source file, tenant, project, title, and page count.
- `document_elements`: ordered scientific elements with page, section, optional bounding box, text, caption, and parent reference.

The HTTP file upload path does not parse PDFs. API routes should create jobs and read persisted results through services and repositories.
