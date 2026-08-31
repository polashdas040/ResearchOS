# File API

Project files are tenant-scoped resources. Binary content is written through the storage provider; metadata is stored in PostgreSQL.

## Endpoints

- `POST /projects/{project_id}/files`
  - Requires bearer authentication.
  - Multipart field: `file`.
  - Supported initial formats: PDF, CSV, JSON, TXT, PNG, JPEG.
  - Returns file metadata including `sha256`, `status`, and `duplicate_of_file_id`.

- `GET /projects/{project_id}/files`
  - Requires project access.
  - Returns paginated non-deleted file metadata.

- `GET /files/{file_id}/download`
  - Requires same organization ownership.
  - Returns file bytes from object storage.

- `DELETE /files/{file_id}`
  - Requires same organization ownership.
  - Soft-deletes metadata and removes object content from the storage provider.

## Validation

Uploads validate filename safety, content type, extension, and maximum size before metadata is stored. Uploaded content is untrusted and is not parsed in the HTTP request path.
