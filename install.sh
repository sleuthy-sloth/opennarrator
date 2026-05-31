#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────
# OpenNarrator — one-command install
# ─────────────────────────────────────────────────────────────────────
# Usage:  bash install.sh
#         bash install.sh --symlink    # also add `on` to /usr/local/bin
# ─────────────────────────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
DO_SYMLINK=false

for arg in "$@"; do
	[ "$arg" = "--symlink" ] && DO_SYMLINK=true
done

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
"$REPO_DIR/.venv/bin/pip" install -q -e "${REPO_DIR}[dev,kokoro,server]" 2>/dev/null ||
	"${REPO_DIR}/.venv/bin/pip" install -e "${REPO_DIR}[kokoro,server]"
echo "✓ OpenNarrator installed"

# ── Global symlink (optional) ───────────────────────────────────────
LINK_NAME="${LINK_NAME:-on}"
LINK_TARGET="/usr/local/bin/$LINK_NAME"

if [ "$DO_SYMLINK" = true ]; then
	if [ -L "$LINK_TARGET" ] || [ ! -e "$LINK_TARGET" ]; then
		echo "   Creating symlink: $LINK_TARGET → opennarrator"
		sudo ln -sf "$REPO_DIR/.venv/bin/opennarrator" "$LINK_TARGET" 2>/dev/null &&
			echo "✓ Now type '$LINK_NAME' anywhere to launch" ||
			echo "⚠️  Could not create symlink (try: sudo bash install.sh --symlink)"
	else
		echo "⚠️  $LINK_TARGET already exists — skipping"
	fi
else
	echo ""
	echo "   💡 Want to launch from anywhere? Re-run:"
	echo "      bash install.sh --symlink"
	echo "      Then just type: [36m${LINK_NAME}[0m"
fi

# ── Done ────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎧 OpenNarrator ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Launch:"
echo "    cd $REPO_DIR && bash run.sh"
echo ""
if [ "$DO_SYMLINK" = true ]; then
	echo "  Or just:"
	echo "    $LINK_NAME"
	echo ""
fi
echo "  CLI:"
echo "    $REPO_DIR/.venv/bin/opennarrator convert book.epub --voice af_bella"
echo ""
