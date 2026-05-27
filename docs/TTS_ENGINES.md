# TTS Engine Comparison

Last updated: 2026-05-27

| Engine | License | Quality | Speed | GPU Required | Voice Cloning | Languages | Model Size |
|--------|---------|---------|-------|-------------|---------------|-----------|------------|
| **F5-TTS** | MIT | ★★★★★ | Fast (GPU) / N/A (CPU) | Yes (CUDA/MPS) | Yes (best open-source cloning) | English (primary), multi-lingual emerging | ~300MB |
| **Piper** | MIT | ★★★☆☆ | Very Fast (CPU) | No | No (50+ pre-trained voices) | 30+ languages | ~50MB per voice |
| **Kokoro** | Apache 2.0 | ★★★★☆ | Fast (CPU) | No | No (pre-trained voices) | English, Japanese, Chinese, Korean, French | ~80MB |
| **XTTSv2** | Non-commercial | ★★★★☆ | Fast (GPU) | Yes | Yes (good cloning) | 16 languages | ~1.8GB |
| **Bark** | MIT | ★★★☆☆ | Slow (GPU) | Yes (heavy) | Yes (speaker prompts) | English, multi-lingual | ~4GB |
| **Coqui TTS** | Apache 2.0 | ★★★☆☆ | Medium | Optional | Yes (XTTS fork) | Multi-lingual | Varies |

## OpenNarrator Support Roadmap

| Engine | v0.1 | v0.2 | v0.3 |
|--------|------|------|------|
| Piper | ✅ Primary | ✅ | ✅ |
| F5-TTS | — | ✅ Voice cloning | ✅ Primary engine |
| Kokoro | — | — | ✅ Additional voices |
| XTTSv2 | — | — | ❌ License incompatible |
| Bark | — | — | ❌ Too slow, too large |

## Why Piper First?

1. **CPU-only** — runs on any machine, no CUDA/MPS setup required
2. **MIT license** — no restrictions
3. **50+ voices** — plenty for testing the pipeline
4. **Subprocess-friendly** — simple CLI interface, easy to isolate
5. **Fast iteration** — ~10x real-time on modern CPU, great for development

The pipeline architecture doesn't care which engine is behind `BaseTTSEngine`. Swapping Piper for F5-TTS in v0.2 is a one-file change.
