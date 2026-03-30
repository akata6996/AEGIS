#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
ENV_FILE="${ROOT_DIR}/.env"
ENV_EXAMPLE="${ROOT_DIR}/../.env.example"

RUN_SERVER=true
if [[ "${1:-}" == "--no-run" ]]; then
  RUN_SERVER=false
fi

cd "${ROOT_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
pip install -e .[dev]

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  echo "Created ${ENV_FILE} from .env.example"
fi

python scripts_init_db.py

if [[ "${RUN_SERVER}" == true ]]; then
  echo "Starting AEGIS gateway at http://127.0.0.1:8000"
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "Environment prepared. Run server with:"
  echo "source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi
