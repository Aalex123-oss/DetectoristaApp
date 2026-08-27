#!/usr/bin/env bash
# Run the FastAPI backend (port 8000) and the Next.js frontend (port 3000) together.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -x backend/.venv/bin/uvicorn ]; then
  echo "backend/.venv is missing - run: bash scripts/setup.sh" >&2
  exit 1
fi

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

cleanup() {
  [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null || true
  [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd backend && .venv/bin/uvicorn app.main:app --reload --port "$BACKEND_PORT") &
BACKEND_PID=$!

npm --prefix frontend run dev -- --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

echo "Backend  -> http://127.0.0.1:${BACKEND_PORT}/docs"
echo "Frontend -> http://localhost:${FRONTEND_PORT}"

wait -n "$BACKEND_PID" "$FRONTEND_PID"
