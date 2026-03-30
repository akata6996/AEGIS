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
uvicorn app.main:app --reload
```

## Current milestone
Phase 1–4 foundations:
- clean module boundaries
- deterministic enforcement pipeline
- schema-first SQLite migration
- verification/rejection log persistence interfaces

