#!/usr/bin/env bash
# Démarre backend (FastAPI) + frontend (Vite) en arrière-plan avec gestion des PID.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS="$ROOT/logs"
mkdir -p "$LOGS"

# Réinitialise les logs à chaque démarrage (pas d'append).
: > "$LOGS/backend.log"
: > "$LOGS/frontend.log"

echo "→ Démarrage du backend (port 8420)…"
cd "$ROOT/backend"
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8420 >> "$LOGS/backend.log" 2>&1 &
echo $! > "$LOGS/backend.pid"

echo "→ Démarrage du frontend (port 8421)…"
cd "$ROOT/frontend"
bun run dev >> "$LOGS/frontend.log" 2>&1 &
echo $! > "$LOGS/frontend.pid"

echo "✓ Lancé. Interface : http://localhost:8421 — API : http://localhost:8420"
