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
   pip install -e .
   cp ../.env.example .env
   python scripts_init_db.py
   ```
4. Configure power: use official/recommended 5V/5A USB-C PSU for Pi 5.
5. Enable service with systemd unit `deploy/aegis-gateway.service`.
