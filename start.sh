#!/usr/bin/env bash
# Démarre backend (FastAPI) + frontend (Vite) en arrière-plan.
# Bootstrap automatique : crée le venv et installe les dépendances si absents.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS="$ROOT/logs"
mkdir -p "$LOGS"

# Rend bun disponible même s'il n'est pas dans le PATH du shell courant.
export PATH="$HOME/.bun/bin:$PATH"

# ---------- Bootstrap backend ----------
cd "$ROOT/backend"
if [ ! -x "venv/bin/uvicorn" ]; then
  echo "→ Configuration du backend (venv + dépendances)…"
  python3 -m venv venv
  ./venv/bin/pip install --quiet --upgrade pip
  ./venv/bin/pip install --quiet -r requirements.txt
fi

# ---------- Bootstrap frontend ----------
cd "$ROOT/frontend"
if ! command -v bun >/dev/null 2>&1; then
  echo "✗ bun introuvable. Installe-le : curl -fsSL https://bun.sh/install | bash"
  exit 1
fi
if [ ! -d "node_modules" ]; then
  echo "→ Installation des dépendances frontend…"
  bun install
fi

# Réinitialise les logs à chaque démarrage (pas d'append).
: > "$LOGS/backend.log"
: > "$LOGS/frontend.log"

echo "→ Démarrage du backend (port 8420)…"
cd "$ROOT/backend"
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8420 >> "$LOGS/backend.log" 2>&1 &
echo $! > "$LOGS/backend.pid"

echo "→ Démarrage du frontend (port 8421)…"
cd "$ROOT/frontend"
bun run dev --host 0.0.0.0 --port 8421 >> "$LOGS/frontend.log" 2>&1 &
echo $! > "$LOGS/frontend.pid"

echo "✓ Lancé. Interface : http://0.0.0.0:8421 — API : http://0.0.0.0:8420"
