<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/OpenNarrator-ffffff?style=for-the-badge&logo=audioboom&logoColor=white&labelColor=1a1a2e&color=e94560">
    <img alt="OpenNarrator" src="https://img.shields.io/badge/OpenNarrator-ffffff?style=for-the-badge&logo=audioboom&logoColor=white&labelColor=1a1a2e&color=16213e">
  </picture>
</div>

<p align="center">
  <i>Open-source audiobook factory — convert any ebook to a chaptered M4B<br>using open-source TTS. No API keys. No vendor lock-in. Just your CPU.</i>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/status-alpha-yellow?style=flat-square" alt="Status: Alpha"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.11+-informational?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey?style=flat-square&logo=apple" alt="macOS"></a>
  <a href="#"><img src="https://img.shields.io/badge/TTS-Kokoro%20(82M)-green?style=flat-square" alt="TTS: Kokoro"></a>
  <a href="#"><img src="https://img.shields.io/badge/ffmpeg-required-orange?style=flat-square&logo=ffmpeg" alt="ffmpeg"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-68%20passing-brightgreen?style=flat-square" alt="Tests: 68 passing"></a>
</p>

---

## 🎧 What is OpenNarrator?

OpenNarrator converts ebooks (EPUB, TXT) into **chaptered M4B audiobooks** using open-source text-to-speech, entirely on your machine.

```bash
pip install opennarrator[kokoro]
opennarrator convert "The Great Gatsby.epub" --voice af_bella --output gatsby.m4b

  ████████████████████████████████████████ 100%
  ✅ Done! 9 chapters, 5h 22m of audio → gatsby.m4b
```

**No ElevenLabs. No AWS Polly. No Google Cloud TTS. No API keys. No usage limits.** Just open-source models and ffmpeg.

### Why OpenNarrator?

| | Commercial TTS | OpenNarrator |
|---|---|---|
| **Cost** | Per-character billing ($100s/year) | **Free** (MIT) |
| **Privacy** | Your book text sent to cloud APIs | **100% offline** |
| **Voice quality** | Excellent | **Good** (Kokoro 82M) |
| **Speed** | Fast networked API | **6x real-time on MPS** |
| **Lock-in** | Cannot switch providers | **Pluggable engines** |
| **Chapters** | Often unsupported | **Full chapter markers** |

---

## ✨ Current Status

> **Phase 3 of 6 complete** — TTS integration live and tested.

### Done ✅
- **Engine selection** — Kokoro (hexgrad/Kokoro-82M) passes quality gate. RTF 0.16x on MPS (10-hour book → ~1.6 hours)
- **EPUB extraction** — Chapter detection, metadata, cover art, Gutenberg boilerplate stripping
- **TXT extraction** — Regex chapter detection (Chapter 1, CHAPTER I, Stave One)
- **Text normalization** — Number-to-words, entity decoding, smart quotes
- **Kokoro TTS engine** — Auto-downloads model on first use, 10 voices, MPS/CUDA/CPU
- **Voice manager** — Voice discovery and resolution
- **Synthesizer** — Rich progress bars, ETA, resume support
- **68 unit tests** — ruff + mypy clean

### Upcoming 🔜
- **ffmpeg assembly** — WAV concatenation, loudness normalization (EBU R128)
- **M4B packager** — Chapter markers, cover art, metadata tags
- **CLI commands** — `convert`, `voices`, `preview`
- **Web UI** — Drag-and-drop FastAPI + Next.js frontend
- **Single-bundle .app** — One-click install (macOS + Windows)

---

## 🚀 Quickstart

```bash
# Prerequisites
brew install ffmpeg           # macOS
# or: sudo apt install ffmpeg  # Linux

# Install OpenNarrator
pip install opennarrator[kokoro]
```

That's it. The TTS model downloads automatically on first use.

```bash
# List available voices
opennarrator voices list

# Convert an EPUB to audiobook
opennarrator convert book.epub --voice af_bella --output book.m4b

# Convert a plain text file
opennarrator convert book.txt --voice am_adam --speed 1.05 --output book.m4b

# Preview a single chapter
opennarrator preview book.epub --chapter 3 --voice af_bella
```

---

## 🗺️ Architecture

```
                    ┌──────────────┐
                    │  Input File  │  EPUB / TXT / PDF
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Extractor   │  ebooklib / regex
                    │  Normalizer  │  numbers → words, clean text
                    └──────┬───────┘
                           │  Chapters[]
                    ┌──────▼───────┐
                    │  Synthesizer │  KokoroEngine (MPS/CPU)
                    │  + Progress  │  Rich progress bars
                    │  + Resume    │  Skip completed chapters
                    └──────┬───────┘
                           │  Per-chapter WAVs
                    ┌──────▼───────┐
                    │   Packager   │  ffmpeg concat + loudnorm
                    │              │  Chapter markers + cover
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  book.m4b    │  🎧 Open in Apple Books
                    └──────────────┘
```

### Engine Architecture

```
BaseTTSEngine (ABC)
  ├── KokoroEngine    ◄── v0.1 (live, Apache 2.0)
  ├── PiperEngine     ──  fallback (fast, CPU-friendly)
  ├── NullEngine      ──  testing (1s silence)
  └── F5TTSEngine     ──  future (best quality, may need GPU)
```

Voices are **bundled in the model** — no separate download. First `synthesize()` call downloads the model from HuggingFace and caches it.

---

## 🎙️ Voices

| Voice | Description | Language |
|-------|-------------|:--------:|
| `af_bella` | American English Female — Bella | 🇺🇸 |
| `af_nicole` | American English Female — Nicole | 🇺🇸 |
| `af_sarah` | American English Female — Sarah | 🇺🇸 |
| `af_sky` | American English Female — Sky | 🇺🇸 |
| `am_adam` | American English Male — Adam | 🇺🇸 |
| `am_michael` | American English Male — Michael | 🇺🇸 |
| `bf_emma` | British English Female — Emma | 🇬🇧 |
| `bf_isabella` | British English Female — Isabella | 🇬🇧 |
| `bm_george` | British English Male — George | 🇬🇧 |
| `bm_lewis` | British English Male — Lewis | 🇬🇧 |

---

## 📊 Performance

| Engine | Device | RTF | 10-hour book |
|--------|:------:|:---:|:------------:|
| **Kokoro** ✅ | MPS (A18 Pro) | **0.16x** | **~1.6 hours** |
| Kokoro | CPU (A18 Pro) | ~0.27x | ~2.7 hours |
| Piper libritts | CPU (Pi 5) | 0.48x | ~4.8 hours |
| KitKat | CPU (Any) | 0.1x | ~1 hour |
| F5-TTS ❌ | MPS (A18 Pro) | 10.48x | ~105 hours |

*RTF = Real-Time Factor. Lower is faster. < 1.0 = faster than real-time.*

---

## 📁 Project Structure

```
opennarrator/
├── src/opennarrator/
│   ├── cli/           # Typer CLI (convert, voices, preview, server)
│   ├── pipeline/      # extractor, normalizer, synthesizer, packager
│   ├── engines/       # base, kokoro, piper, f5_tts (pluggable)
│   ├── audio/         # ffmpeg wrapper, loudness normalization
│   ├── voice/         # manager, registry
│   ├── config.py      # Pydantic settings (YAML + env overrides)
│   ├── types.py       # Chapter, BookMetadata, Voice, ConversionJob
│   └── exceptions.py  # OpenNarratorError hierarchy
├── tests/             # 68 unit tests
├── docs/              # SPEC, implementation plan, engine comparison
└── spikes/            # Feasibility studies (Piper, Kokoro, F5-TTS)
```

---

## 🧑‍💻 Contributing

OpenNarrator is in active early development. Best ways to help:

1. **Test voices** — Listen to samples and report quality
2. **Try it on your books** — Open issues for edge cases (weird EPUBs, long books)
3. **Suggest engines** — Know a great open-source TTS engine? Open an issue
4. **Web UI** — Phase 2 will need frontend contributors

---

## 📜 License

MIT © 2026 Sleuthy-Sloth

OpenNarrator is free and open-source. The Kokoro TTS engine is Apache 2.0. Other engines have their own licenses — check before commercial use.

---

<p align="center">
  <sub>Built with 🎙️ by <a href="https://github.com/sleuthy-sloth">Sleuthy-Sloth</a></sub>
</p>
