# PLAN 05 File Storage

PLAN 05 introduces a tenant-scoped project file platform.

## Design

- PostgreSQL remains the source of truth for file metadata.
- Object content goes through the `ObjectStorage` interface.
- API routes stay thin and delegate authorization and validation to `FileService`.
- Project ownership is checked through `ProjectService` before upload or listing.
- File download/delete access is scoped by the authenticated user's primary organization.

## Current Adapter

The default development storage adapter is in-memory. This keeps the phase small and testable without adding a new S3 SDK dependency before worker/document ingestion phases. The storage interface is ready for a MinIO/S3 adapter.

## Limits

- Maximum upload size is 25 MB.
- Supported initial types are PDF, CSV, JSON, TXT, PNG, and JPEG.
- Files are marked `READY` after upload because background processing starts in PLAN 06.
