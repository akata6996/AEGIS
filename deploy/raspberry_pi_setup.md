# Raspberry Pi 5 Deployment (Local-First)

1. Install OS and update:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. Install Mosquitto:
   ```bash
   sudo apt install -y mosquitto mosquitto-clients
   sudo systemctl enable --now mosquitto
   ```
3. Clone repository and setup gateway:
   ```bash
   git clone <repo-url> /opt/aegis
   cd /opt/aegis/gateway
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   cp ../.env.example .env
   python scripts_init_db.py
   ```
4. Configure power: use official/recommended 5V/5A USB-C PSU for Pi 5.
5. Enable service with systemd unit `deploy/aegis-gateway.service`.

## Health checks
```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/dashboard/overview
```

## Logs
```bash
sudo journalctl -u aegis-gateway -f
sudo journalctl -u mosquitto -f
```

## Backup/export verification artifacts
```bash
# consistent SQLite backup
sqlite3 /opt/aegis/gateway/data/aegis.db ".backup /opt/aegis/backups/aegis_$(date +%F_%H%M).db"

# export core evidence tables
sqlite3 -header -csv /opt/aegis/gateway/data/aegis.db "SELECT * FROM verification_log;" > /opt/aegis/backups/verification_log.csv
sqlite3 -header -csv /opt/aegis/gateway/data/aegis.db "SELECT * FROM merkle_batch_metadata;" > /opt/aegis/backups/merkle_batches.csv
sqlite3 -header -csv /opt/aegis/gateway/data/aegis.db "SELECT * FROM anchor_attempts;" > /opt/aegis/backups/anchor_attempts.csv
```
