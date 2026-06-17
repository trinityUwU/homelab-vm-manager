#!/usr/bin/env bash
# Redémarre proprement : stop puis start.
ROOT="$(cd "$(dirname "$0")" && pwd)"
"$ROOT/stop.sh"
sleep 1
"$ROOT/start.sh"
