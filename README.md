<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/OpenNarrator-ffffff?style=for-the-badge&logo=audioboom&logoColor=white&labelColor=1a1a2e&color=e94560">
    <img alt="OpenNarrator" src="https://img.shields.io/badge/OpenNarrator-ffffff?style=for-the-badge&logo=audioboom&logoColor=white&labelColor=1a1a2e&color=16213e">
  </picture>
</div>

<p align="center">
  <i>Open-source audiobook factory — convert any ebook to a chaptered M4B<br>using open-source TTS. No API keys. No vendor lock-in. Just your machine.</i>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/status-v0.1--alpha-yellow?style=flat-square" alt="Status: v0.1-alpha"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.11+-informational?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey?style=flat-square&logo=apple" alt="macOS"></a>
  <a href="#"><img src="https://img.shields.io/badge/TTS-Kokoro%20(82M)-green?style=flat-square" alt="TTS: Kokoro"></a>
  <a href="#"><img src="https://img.shields.io/badge/ffmpeg-required-orange?style=flat-square&logo=ffmpeg" alt="ffmpeg"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-78%20passing-brightgreen?style=flat-square" alt="Tests: 78 passing"></a>
  <a href="#"><img src="https://img.shields.io/badge/UI-web+CLI-blueviolet?style=flat-square" alt="Web + CLI"></a>
</p>

---

## 🎧 What is OpenNarrator?

OpenNarrator converts ebooks (EPUB, TXT) into **chaptered M4B audiobooks** using open-source text-to-speech, entirely on your machine.

```bash
opennarrator                         # → opens http://localhost:8080
```

Drop an ebook in the browser — get an M4B back. Or use the CLI:

```bash
opennarrator convert book.epub --voice af_bella --output book.m4b

  ████████████████████████████████████████ 100%
  ✅ Done! 9 chapters, 5h 22m of audio → book.m4b
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

## 🚀 Quickstart

### Prerequisites

```bash
brew install ffmpeg           # macOS
# or: sudo apt install ffmpeg  # Linux
```

### Install

```bash
git clone git@github.com:sleuthy-sloth/opennarrator.git
cd opennarrator
bash install.sh --symlink     # creates `on` command globally
```

### Launch

```bash
on                            # opens http://localhost:8080 🎧
```

Or from the repo:

```bash
bash run.sh                   # auto-installs, auto-launches
```

The TTS model (~82M params + spaCy pipeline) downloads automatically on first conversion. Everything is cached — subsequent launches are instant.

### CLI

```bash
opennarrator convert book.epub --voice af_bella --output book.m4b
opennarrator convert book.txt --voice am_adam --speed 1.05
opennarrator voices list
opennarrator voices info af_bella
```

---

## 🌐 Web UI

```
http://localhost:8080
```

| Feature | |
|---|---|
| Drag-and-drop upload | Drop EPUB or TXT files |
| Voice selector | All 10 Kokoro voices with descriptions |
| Real-time progress | SSE-powered live progress bar + chapter status |
| Job history | Sidebar with status, progress, and downloads |
| Download | One-click M4B download on completion |

<p align="center">
  <i>Dark theme · warm amber accents · responsive layout</i>
</p>

---

## 🏗️ Architecture

```
                    ┌──────────────┐
                    │  Input File  │  EPUB / TXT / PDF
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Extractor   │  ebooklib / regex chapter detection
                    │  Normalizer  │  numbers→words, entity decode, quotes
                    └──────┬───────┘
                           │  Chapters[]
                    ┌──────▼───────┐
                    │  Synthesizer │  KokoroEngine (MPS/CPU, 6x real-time)
                    │  + Progress  │  Rich progress bars + resume
                    │  + SSE       │  Real-time web progress stream
                    └──────┬───────┘
                           │  Per-chapter WAVs
                    ┌──────▼───────┐
                    │   Packager   │  ffmpeg loudnorm + concat + AAC
                    │              │  Chapter markers + cover art + metadata
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  book.m4b    │  🎧 Open in Apple Books
                    └──────────────┘
```

### Engine Architecture (Pluggable)

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
| F5-TTS ❌ | MPS (A18 Pro) | 10.48x | ~105 hours (too slow) |

*RTF = Real-Time Factor. Lower is faster. < 1.0 = faster than real-time.*

---

## 📁 Project Structure

```
opennarrator/
├── src/opennarrator/
│   ├── cli/           # Typer CLI (convert, voices, server)
│   ├── pipeline/      # Extractor, normalizer, synthesizer, packager
│   ├── engines/       # Base, kokoro, null (pluggable TTS)
│   ├── audio/         # FFmpeg wrapper, loudness normalization
│   ├── voice/         # Manager, registry
│   ├── server/        # FastAPI + static frontend
│   ├── config.py      # Pydantic settings (YAML + env overrides)
│   ├── types.py       # Chapter, BookMetadata, Voice, ConversionJob
│   └── exceptions.py  # OpenNarratorError hierarchy
├── tests/             # 78 unit tests
├── docs/              # SPEC, implementation plan, engine comparison
├── spikes/            # Feasibility studies (Piper, Kokoro, F5-TTS)
├── install.sh         # One-command setup
└── run.sh             # One-command launch
```

---

## 📜 License

MIT © 2026 Sleuthy-Sloth

OpenNarrator is free and open-source. The Kokoro TTS engine is Apache 2.0. Other engines have their own licenses — check before commercial use.

---

<p align="center">
  <sub>Built with 🎙️ by <a href="https://github.com/sleuthy-sloth">Sleuthy-Sloth</a></sub>
</p>
