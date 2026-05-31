#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────
# OpenNarrator — one-command launch
# ─────────────────────────────────────────────────────────────────────
# Usage:  bash run.sh              # launch web UI on :8080
#         bash run.sh --port 9090  # custom port
#         bash run.sh --cli ...    # pass args to CLI instead
# ─────────────────────────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT=".venv/bin/opennarrator"

# ── Auto-install ─────────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/$SCRIPT" ]; then
	echo "⚙️  First-time setup — installing..."
	bash "$REPO_DIR/install.sh"
	echo ""
fi

# ── Check ffmpeg ────────────────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
	echo "ℹ️  Install ffmpeg for audio processing:"
	echo "   macOS: brew install ffmpeg"
	echo "   Linux: sudo apt install ffmpeg"
	echo ""
fi

# ── Launch ───────────────────────────────────────────────────────────
# Run opennarrator with all args (no args = launch web UI by default)
exec "$REPO_DIR/$SCRIPT" "$@"
