# AEGIS Implementation Plan

## 1) High-level roadmap
1. Foundation: repo setup, env config, migrations, service skeleton.
2. Domain model: schemas for ingestion/enforcement/logging/anchoring.
3. Gateway core: MQTT ingestion -> enforcement -> persistence transaction.
4. Cryptographic layer: hash chaining, Merkle batching, proof storage.
5. Anchoring layer: asynchronous Solana Devnet JSON-RPC client with retry.
6. Verification workspace: independent recomputation APIs.
7. Threat scenario testing: replay, delay, discontinuity, outage, normal traffic.
8. Deployment/observability: Raspberry Pi scripts, systemd, health endpoints.

## 2) Recommended stack
- Gateway backend: Python 3.11 + FastAPI + SQLAlchemy + Alembic.
- MQTT: paho-mqtt with QoS 1 subscriptions.
- DB: SQLite (WAL mode, strict transactions).
- Frontend: server-rendered operator pages from FastAPI templates (phase 1) then React optional.
- ESP32 firmware: Arduino C++ (faster onboarding for thesis teams).

## 3) Repository structure
```
/gateway
  /app
    /api
    /anchor
    /core
    /dashboard
    /db
    /enforcement
    /ingestion
    /logging
    /merkle
    /verification
  /migrations
  /tests
/docs
/deploy
/sensor_firmware/arduino
```

## 4) Schema inventory
Tables:
- enrollment_registry
- session_state
- verification_log
- rejection_log
- merkle_batch_metadata
- merkle_leaves
- merkle_proofs
- anchor_attempts
- operator_reset_events

See `gateway/migrations/0001_initial.sql` for constraints and indexes.

## 5) MQTT contract
- Topic: `aegis/nodes/{node_id}/telemetry`
- QoS: 1
- Payload fields:
  - `node_id` (string)
  - `seq_num` (non-negative integer)
  - `timestamp` (ISO 8601 UTC)
  - `sensor_value` (number)
  - `sensor_type` (optional string)
  - `unit` (optional string)

## 6) Backend module sequencing
1. ingestion service
2. enforcement engine
3. persistence layer
4. merkle builder
5. solana anchor client
6. verification api
7. dashboard api

## 7) Threat test matrix
- replay attack -> rejection_log: duplicate/old sequence.
- delayed injection -> bounded delay rejection.
- sequence discontinuity -> deterministic reject + session flag.
- MQTT interruption -> session continuity warning/reject policy.
- benign traffic -> admitted and hash-linked.
- edge cases -> duplicates, skipped sequence, stale timestamps.

## 8) Raspberry Pi deployment
- Install Mosquitto locally.
- Create Python venv for gateway service.
- Initialize SQLite DB via SQL migration.
- Configure `.env` and systemd services.
- Expose API only on trusted local network.

## 9) Coding tasks in order
1. config + packet model validation.
2. DB migration and repositories.
3. deterministic enforcement service.
4. MQTT subscriber service and pipeline glue.
5. API endpoints for logs, health, verification.
6. merkle + anchoring workers.
7. tests and threat simulation scripts.
