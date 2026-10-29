#!/bin/bash
# Deploy COFA FORWARD to the MacBook Pro as a native macOS app with an offline cache.
#
#  1. rsync this repo to the MBP (source + config; data/ is built there),
#  2. install the Python venv (uv sync),
#  3. prefetch the offline snapshot (optional; --snapshot),
#  4. build the SwiftUI shell and assemble "COFA Forward.app".
#
# Usage:
#   scripts/deploy_macos_app.sh [--host HOST] [--snapshot] [--tiles] [--no-venv]
#
set -euo pipefail

HOST="${HOST:-bens-macbook-pro.local}"
REMOTE_USER="${REMOTE_USER:-ben}"
DO_SNAPSHOT=0
DO_TILES=0
DO_VENV=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --snapshot) DO_SNAPSHOT=1; shift ;;
    --tiles) DO_TILES=1; shift ;;
    --no-venv) DO_VENV=0; shift ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE="$REMOTE_USER@$HOST"

echo "==> rsync repo → $REMOTE:~/cofa-forward"
rsync -az --delete -e "ssh -o ConnectTimeout=15 -o ServerAliveInterval=15" \
  --exclude '.git' \
  --exclude '.build' \
  --exclude '.venv' \
  --exclude 'apps/web/node_modules' \
  --exclude 'data/cache' \
  --exclude 'data/raw' \
  --exclude 'data/snapshot' \
  --exclude 'data/tiles' \
  --exclude '__pycache__' \
  "$ROOT/" "$REMOTE:~/cofa-forward/"

if [[ "$DO_VENV" -eq 1 ]]; then
  echo "==> install Python venv on $HOST (uv sync)"
  ssh "$REMOTE" 'export PATH="$HOME/.local/bin:$PATH"; cd ~/cofa-forward && uv sync'
fi

if [[ "$DO_SNAPSHOT" -eq 1 ]]; then
  echo "==> prefetch offline snapshot on $HOST"
  ssh "$REMOTE" 'export PATH="$HOME/.local/bin:$PATH"; cd ~/cofa-forward && uv run python scripts/prefetch_snapshot.py --skip-ibtracs'
fi

if [[ "$DO_TILES" -eq 1 ]]; then
  echo "==> prefetch offline basemap tiles on $HOST"
  ssh "$REMOTE" 'export PATH="$HOME/.local/bin:$PATH"; cd ~/cofa-forward && uv run python scripts/prefetch_tiles.py'
fi

echo "==> build SwiftUI shell on $HOST"
ssh "$REMOTE" 'cd ~/cofa-forward/apps/macos && ./package_app.sh'

echo "==> copy app to /Applications on $HOST"
ssh "$REMOTE" 'rm -rf "/Applications/COFAHUB.app"; cp -R ~/cofa-forward/apps/macos/"COFAHUB.app" /Applications/'

echo "✅ Done. Launch \"COFAHUB\" on $HOST (serves the React app + API on 127.0.0.1:8700)."
