#!/usr/bin/env bash
# Provision the full Detectorista Web GIS workspace (backend venv + frontend packages).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Creating backend virtual environment (backend/.venv)"
"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements.txt

if [ ! -f backend/.env ]; then
  echo "==> Seeding backend/.env from backend/.env.example"
  cp backend/.env.example backend/.env
fi

echo "==> Installing frontend packages"
npm --prefix frontend install

if [ ! -f frontend/.env.local ]; then
  echo "==> Seeding frontend/.env.local from frontend/.env.example"
  cp frontend/.env.example frontend/.env.local
fi

echo "==> Running backend test suite"
(cd backend && .venv/bin/pytest -q)

echo
echo "Setup complete. Start both services with: npm run dev"
