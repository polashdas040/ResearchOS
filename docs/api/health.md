# Health API

## `GET /health`

Returns process liveness.

```json
{
  "status": "ok"
}
```

## `GET /ready`

Returns dependency readiness for PostgreSQL, Redis, ChromaDB, and object storage.

When every dependency is reachable, the endpoint returns HTTP 200 with `status: "ok"`. When any dependency is unreachable, it returns HTTP 503 with dependency details.
