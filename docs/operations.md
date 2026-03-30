# AEGIS Operations & Observability

## Background pipeline worker
The gateway starts a periodic worker that performs:
1. Merkle aggregation of unbatched admitted records.
2. Asynchronous attempt to anchor pending Merkle roots.

This worker is non-gating: ingestion continues even if anchoring fails.

## Dashboard APIs
- `GET /api/v1/dashboard/overview`
- `GET /api/v1/dashboard/rejections/recent?limit=20`
- `GET /api/v1/dashboard/anchors/recent?limit=20`

## Operator API
- `POST /api/v1/operator/sessions/{node_id}/reset`

This is the only allowed path for explicit sequence/session reset and produces an `operator_reset_events` audit record.
