#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────
# OpenNarrator — Hugging Face Spaces entry point
# ─────────────────────────────────────────────────────────────────────

PORT="${PORT:-7860}"
DEVICE="${OPENNARRATOR_DEVICE:-cpu}"

echo "🎧 OpenNarrator starting on port $PORT (device: $DEVICE)"

# Start the FastAPI server with uvicorn
cd /app
exec uvicorn opennarrator.server.app:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --workers 1
