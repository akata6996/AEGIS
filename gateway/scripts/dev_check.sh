#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

if [[ ! -d .venv ]]; then
  echo "Missing .venv. Run scripts/dev_up.sh --no-run first."
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

python scripts_init_db.py
pytest -q
curl -fsS http://127.0.0.1:8000/api/v1/health || true
