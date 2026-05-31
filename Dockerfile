# ─────────────────────────────────────────────────────────────────────
# OpenNarrator — Hugging Face Spaces Dockerfile
# ─────────────────────────────────────────────────────────────────────
# Build:  docker build -t opennarrator .
# Run:    docker run -p 7860:7860 opennarrator
# ─────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# ── System dependencies ─────────────────────────────────────────────
RUN apt-get update -qq && apt-get install -y -qq \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# ── Install OpenNarrator ────────────────────────────────────────────
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install core + kokoro + server deps (CPU-only PyTorch for smaller image)
RUN pip install --quiet --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --quiet --no-cache-dir -e ".[kokoro,server]" \
    && python3 -c "import kokoro; print('Kokoro OK')" 2>/dev/null || true

# ── Environment ─────────────────────────────────────────────────────
ENV HF_HOME=/data/.cache/huggingface
ENV OPENNARRATOR_DEVICE=cpu
ENV GRADIO_SERVER_NAME=0.0.0.0
EXPOSE 7860

# ── Entry point ─────────────────────────────────────────────────────
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
