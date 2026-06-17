#!/usr/bin/env bash
# Arrête backend et frontend via leurs fichiers PID.
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS="$ROOT/logs"

for name in backend frontend; do
  pidfile="$LOGS/$name.pid"
  if [ -f "$pidfile" ]; then
    pid="$(cat "$pidfile")"
    if kill "$pid" 2>/dev/null; then
      echo "✓ $name arrêté (PID $pid)"
    fi
    rm -f "$pidfile"
  else
    echo "· $name : aucun PID enregistré"
  fi
done
# Filet de sécurité pour les processus enfants (vite, uvicorn reload).
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
