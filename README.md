# AEGIS Thesis Prototype

AEGIS is a local-first research prototype for acquisition-time verifiability in commodity IoT networks.

## Scope
- ESP32 nodes publish telemetry using MQTT QoS 1.
- Raspberry Pi 5 gateway runs Mosquitto + AEGIS services.
- Gateway enforces temporal/sequence/session checks before persistence.
- Admitted records are hash-linked in SQLite append-only log.
- Every 10 minutes admitted records are batched into a Merkle tree and rooted asynchronously to Solana Devnet.

## Repository Layout
- `gateway/`: Python gateway backend.
- `sensor_firmware/arduino/`: ESP32 firmware skeleton.
- `deploy/`: Raspberry Pi setup and systemd assets.
- `docs/`: architecture and schema documentation.

## Quick start
```bash
cd gateway
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp ../.env.example .env
python scripts_init_db.py
uvicorn app.main:app --reload
```

## Current milestone
Phase 1–8 implementation in progress (current baseline):
- clean module boundaries
- deterministic enforcement pipeline
- schema-first SQLite migration
- Merkle batch generation + stored proofs
- async-style anchor orchestration with retry logging (mock-by-default for Devnet-safe testing)
- verification workspace APIs for chain/proof/root/anchor checks

- operator session reset endpoint + reset event logging
- repeatable threat scenario runner with latency measurements
- deployment health checks and evidence backup/export procedures
