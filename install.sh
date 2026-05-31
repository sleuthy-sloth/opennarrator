#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────
# OpenNarrator — one-command install
# ─────────────────────────────────────────────────────────────────────
# Usage:  curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash
#         or just: bash install.sh
# ─────────────────────────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"

echo "🎧 OpenNarrator — one-command install"
echo ""

# ── Check Python ────────────────────────────────────────────────────
if ! command -v "$PYTHON" &>/dev/null; then
    echo "❌ Python not found. Install Python 3.11+ first."
    echo "   macOS: brew install python@3.11"
    exit 1
fi

PY_VERSION=$("$PYTHON" --version 2>&1 | grep -oP '\d+\.\d+')
echo "✓ Python $PY_VERSION detected"

# ── Check ffmpeg ────────────────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
    echo ""
    echo "⚠️  ffmpeg not found. Install it:"
    echo "   macOS: brew install ffmpeg"
    echo "   Linux: sudo apt install ffmpeg"
    echo ""
fi

# ── Create virtual environment ──────────────────────────────────────
if [ ! -d "$REPO_DIR/.venv" ]; then
    echo "   Creating virtual environment..."
    "$PYTHON" -m venv "$REPO_DIR/.venv"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# ── Install package ─────────────────────────────────────────────────
echo "   Installing OpenNarrator with all extras..."
"$REPO_DIR/.venv/bin/pip" install -q -e "${REPO_DIR}[dev,kokoro,server]" 2>/dev/null || "${REPO_DIR}/.venv/bin/pip" install -e "${REPO_DIR}[kokoro,server]"
echo "✓ OpenNarrator installed"

# ── Done ────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎧 OpenNarrator ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Launch the web UI:"
echo "    cd $REPO_DIR && bash run.sh"
echo ""
echo "  Or use the CLI:"
echo "    $REPO_DIR/.venv/bin/opennarrator --help"
echo ""
