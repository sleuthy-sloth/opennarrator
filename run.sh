#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────
# OpenNarrator — launch the web UI
# ─────────────────────────────────────────────────────────────────────
# Usage:  bash run.sh
#         bash run.sh --port 9090
#         bash run.sh --no-browser
# ─────────────────────────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${1:-8080}"
OPEN_BROWSER=true

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --port=*) PORT="${arg#*=}" ;;
        --port) ;;  # handled by positional
        --no-browser|--no-open) OPEN_BROWSER=false ;;
    esac
done

# ── Ensure installed ─────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/.venv/bin/opennarrator" ]; then
    echo "⚙️  First-time setup — installing..."
    bash "$REPO_DIR/install.sh"
    echo ""
fi

# ── Ensure ffmpeg ────────────────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
    echo "⚠️  ffmpeg is required. Install it:"
    echo "   macOS: brew install ffmpeg"
    echo "   Linux: sudo apt install ffmpeg"
    echo ""
fi

# ── Launch ───────────────────────────────────────────────────────────
echo "🎧 OpenNarrator"
echo "   Server: http://localhost:${PORT}"
echo "   Press Ctrl+C to stop."
echo ""

if [ "$OPEN_BROWSER" = true ]; then
    "$REPO_DIR/.venv/bin/opennarrator" server --port "$PORT"
else
    "$REPO_DIR/.venv/bin/opennarrator" server --port "$PORT" --no-open
fi
