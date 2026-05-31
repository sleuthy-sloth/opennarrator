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
  <a href="#"><img src="https://img.shields.io/badge/formats-EPUB%20TXT%20DOCX-blue?style=flat-square" alt="Formats: EPUB TXT DOCX"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-85%20passing-brightgreen?style=flat-square" alt="Tests: 85 passing"></a>
</p>

---

## 🎧 What is OpenNarrator?

OpenNarrator converts ebooks (EPUB, TXT, DOCX) into **chaptered M4B audiobooks** using open-source text-to-speech, entirely on your machine.

```bash
on                      # → opens http://localhost:8080
```

Drop an ebook in the browser — preview voices with a click, adjust speed with a slider, and download a chaptered M4B. Or use the CLI:

```bash
opennarrator convert book.epub --voice af_bella --speed 1.1
opennarrator preview af_bella          # hear a voice sample
opennarrator voices list                # list all voices
```

**No ElevenLabs. No AWS Polly. No Google Cloud TTS. No API keys.** Just open-source models and ffmpeg.

---

## 🚀 Quickstart

```bash
brew install ffmpeg                         # macOS: one-time
git clone git@github.com:sleuthy-sloth/opennarrator.git
cd opennarrator
bash install.sh --symlink                   # creates `on` command

on                                          # launch web UI
```

The TTS model downloads automatically on first conversion. All subsequent launches are instant.

### What you can convert

| Format | Chapter detection |
|--------|:-----------------:|
| EPUB | TOC-based (ebooklib) |
| TXT | Regex (`Chapter 1`, `CHAPTER I`, `Stave One`, etc.) |
| DOCX | Heading styles (Heading 1, Heading 2, ...) |

---

## 🌐 Web UI

`on` opens a dark-themed audiobook factory at `http://localhost:8080`:

| Feature | Description |
|---|---|
| **Voice Gallery** | Voice cards with inline play buttons — click to hear any voice before converting |
| **Speed Slider** | 0.5x – 2.0x speech rate, real-time label update |
| **Drag & Drop** | EPUB / TXT / DOCX — format badges in drop zone |
| **Chapter Timeline** | Live per-chapter progress during conversion with animated status dots |
| **Job History** | Persists across page refreshes via localStorage |
| **Advanced Settings** | Resume toggle, keep WAVs option |
| **Real-time Progress** | SSE-powered progress bar with ETA |

Each voice preview generates a ~10-second sample from Jane Austen's *Pride and Prejudice* — cached so subsequent plays are instant.

---

## 🎙️ Voices

| Voice | Description | 
|-------|-------------|
| `af_bella` | American English Female — Bella |
| `af_nicole` | American English Female — Nicole |
| `af_sarah` | American English Female — Sarah |
| `af_sky` | American English Female — Sky |
| `am_adam` | American English Male — Adam |
| `am_michael` | American English Male — Michael |
| `bf_emma` | British English Female — Emma |
| `bf_isabella` | British English Female — Isabella |
| `bm_george` | British English Male — George |
| `bm_lewis` | British English Male — Lewis |

Preview any voice: `on preview af_bella` or click the play button in the Web UI.

---

## 📊 Performance

| Engine | Device | RTF | 10-hour book |
|--------|:------:|:---:|:------------:|
| **Kokoro** | MPS (A18 Pro) | **0.16x** | **~1.6 hours** |
| Kokoro | CPU (A18 Pro) | ~0.27x | ~2.7 hours |
| Piper libritts | CPU (Pi 5) | 0.48x | ~4.8 hours |
| F5-TTS | MPS (A18 Pro) | 10.48x | ❌ too slow |

---

## 🏗️ Architecture

```
Input File (EPUB / TXT / DOCX)
        │
        ▼
   Extractor ────► Chapters[] + Metadata
        │
        ▼
   Normalizer ───► Numbers→words, entities, quotes
        │
        ▼
   KokoroEngine ──► Per-chapter WAV files
   (MPS/CPU,      │  Speed control (0.5x–2.0x)
    6x real-time) │  Resume support
        │
        ▼
   Packager ─────► ffmpeg loudnorm + concat + AAC
                   Chapter markers + cover art + metadata
        │
        ▼
      book.m4b 🎧
```

---

## 📁 Project Structure

```
opennarrator/
├── src/opennarrator/
│   ├── cli/           # convert, preview, voices, server
│   ├── pipeline/      # extractor, normalizer, synthesizer, packager
│   ├── engines/       # BaseTTSEngine, KokoroEngine, NullEngine
│   ├── audio/         # FFmpeg wrapper (loudnorm, concat, M4B)
│   ├── voice/         # Manager, registry
│   ├── server/        # FastAPI + static frontend
│   ├── config.py, types.py, exceptions.py
├── tests/             # 85 unit tests
├── spikes/            # Piper, Kokoro, F5-TTS feasibility studies
├── install.sh         # One-command setup
└── run.sh             # One-command launch
```

---

## 📜 License

MIT © 2026 Sleuthy-Sloth. Kokoro TTS is Apache 2.0.

<p align="center">
  <sub>Built with 🎙️ by <a href="https://github.com/sleuthy-sloth">Sleuthy-Sloth</a></sub>
</p>
