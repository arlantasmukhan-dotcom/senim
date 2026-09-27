#!/usr/bin/env bash
# Starts SENIM in one terminal: the FastAPI backend (http://127.0.0.1:8000) and the
# Next.js site (http://localhost:3000). First run installs dependencies and creates .env.
# Ports: BACKEND_PORT=8000 WEB_PORT=3000 by default, e.g. `WEB_PORT=3001 ./start.sh`.
# Works without API keys: every screen works, checking turns on once .env has OPENROUTER_API_KEY.
set -euo pipefail
cd "$(dirname "$0")"
BACKEND_PORT="${BACKEND_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

if [ ! -d .venv ]; then
  echo "Creating Python environment (.venv)…"
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example (add OPENROUTER_API_KEY to enable checking)."
fi

if [ ! -d web/node_modules ]; then
  echo "Installing web dependencies…"
  (cd web && npm install)
fi

.venv/bin/uvicorn senim.app:app --reload --port "$BACKEND_PORT" &
BACKEND=$!
trap 'kill "$BACKEND" 2>/dev/null || true' EXIT INT TERM

echo "Backend: http://127.0.0.1:$BACKEND_PORT   Site: http://localhost:$WEB_PORT   (Ctrl+C stops both)"
cd web && SENIM_API_URL="http://127.0.0.1:$BACKEND_PORT" npm run dev -- -p "$WEB_PORT"
