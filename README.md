<!--
────────────────────────────────────────────────────────────────
  OpenNarrator — Break the audiobook monopoly with open-source TTS
────────────────────────────────────────────────────────────────
-->

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/OpenNarrator-ffffff?style=for-the-badge&logo=audioboom&logoColor=white&labelColor=1a1a2e&color=e94560">
    <img alt="OpenNarrator" src="https://img.shields.io/badge/OpenNarrator-ffffff?style=for-the-badge&logo=audioboom&logoColor=white&labelColor=1a1a2e&color=16213e">
  </picture>
</p>

<p align="center">
  <i>Convert any ebook into a professional audiobook — no API keys, no per-character billing,<br>no vendor lock-in. Just open-source TTS and ffmpeg.</i>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/status-pre--alpha-red?style=flat-square" alt="Status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.12+-informational?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square&logo=apple" alt="macOS"></a>
  <a href="#"><img src="https://img.shields.io/badge/TTS-Piper%20%7C%20Kokoro%20%7C%20F5--TTS-green?style=flat-square" alt="TTS Engines"></a>
  <a href="#"><img src="https://img.shields.io/badge/ffmpeg-required-orange?style=flat-square&logo=ffmpeg" alt="ffmpeg"></a>
</p>

---

## 🎧 What is OpenNarrator?

OpenNarrator is a **command-line audiobook factory**. Point it at an EPUB, PDF, or text file and it produces a chaptered M4B file — the standard audiobook format — using open-source text-to-speech engines running entirely on your machine.

No ElevenLabs. No AWS Polly. No Google Cloud Text-to-Speech. No API keys. No usage limits. Just your CPU and open-source models.

```
$ opennarrator convert "The Great Gatsby.epub" --voice hfc_female --output gatsby.m4b

  ████████████████████████████████████████ 100%
  ✅ Done! 9 chapters, 5h 22m of audio → gatsby.m4b
```

---

## 🗺️ Roadmap

```
v0.1.0 (current)          v0.2.0               v0.3.0              v1.0.0
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ 🏗️ Pipeline MVP  │  │ 🎙️ Voice Cloning │  │ 🌐 Web UI        │  │ 📦 .app Bundle   │
│                 │  │                 │  │                 │  │                 │
│ • EPUB/TXT→M4B  │  │ • F5-TTS engine │  │ • Drag & drop   │  │ • Single-click   │
│ • Piper engine  │  │ • Clone voice   │  │ • Job queue     │  │   install        │
│ • Chapter marks │  │   from 30s WAV  │  │ • Preview pane  │  │ • Auto-update    │
│ • Resume support│  │ • Quality presets│  │ • Progress live │  │ • Voice packs    │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
     Q3 2026              Q4 2026              Q1 2027              Q2 2027
```

### Detailed v0.1.0 Plan

| Phase | Tasks | Status |
|-------|-------|--------|
| **0. Engine Selection** — Voice quality gate, test `libritts` and Kokoro, commit to engine | 4 | 🔬 In Progress |
| **1. Skeleton** — Scaffolding, types, abstract engine interface, config system | 4 | ⬜ Blocked by Phase 0 |
| **2. Input Pipeline** — EPUB/TXT extraction, chapter detection, text normalization | 3 | ⬜ Pending |
| **3. TTS Integration** — Engine adapter, voice manager, synthesizer with resume | 3 | ⬜ Pending |
| **4. Audio Assembly** — ffmpeg concat, loudness normalization, M4B packaging | 3 | ⬜ Pending |
| **5. CLI & Ship** — `convert`/`voices` commands, README, smoke tests | 4 | ⬜ Pending |

**Why Phase 0 first?** Voice quality is the #1 risk. If the voice sounds robotic, users won't listen for hours, and the tool fails regardless of technical correctness. We're testing `en_US-libritts` (audiobook-trained) and Kokoro before committing to an engine. See [Voice Quality Requirements](docs/SPEC.md#voice-quality-requirements).

### TTS Engine Strategy

| Engine | License | Quality | CPU? | Cloning? | Target |
|--------|---------|---------|:----:|:--------:|--------|
| **Piper** | MIT | ★★★☆☆ ⚠️ | ✅ | ❌ | v0.1 candidate (`lessac` robotic, testing `libritts`) |
| **Kokoro** | Apache 2.0 | ★★★★☆ | ✅ | ❌ | v0.1 candidate (testing on MacBook Neo) |
| **F5-TTS** | MIT | ★★★★★ | ⚠️ | ✅ | v0.2 — best quality + voice cloning (GPU may be required) |

**Current Status:** Engine selection in progress. Piper's `en_US-lessac` voice failed quality gate (testers would not listen to a 10-hour book in this voice). Testing `en_US-libritts` (audiobook-trained) and Kokoro next. See [Spike Results](#-spike-results) and [Voice Quality Gate](docs/SPEC.md#voice-quality-gate).

---

## 🏗️ Architecture

```
Input File (EPUB/PDF/TXT)
        │
        ▼
   Extractor ────► Chapters[] + Metadata
        │
        ▼
   Normalizer ───► Cleaned text, number expansion
        │
        ▼
   Synthesizer ──► Per-chapter WAV files ──► Resume-safe
        │              │
        │         TTS Engine (pluggable: Piper / Kokoro / F5-TTS)
        │
        ▼
   Packager ─────► ffmpeg concat + normalize + chapters → M4B
```

**Key design decisions:**
- **Pluggable engines** — swap TTS backends via abstract `BaseTTSEngine`
- **Subprocess isolation** — each chapter runs in its own process (GPU memory safety)
- **WAV intermediates** — lossless, cheap, enables resume-after-failure
- **ffmpeg for assembly** — industry standard for M4B + chapter markers

---

## 🚀 Quickstart

> **Note:** OpenNarrator is pre-alpha and engine selection is in progress. The quickstart shows the target experience. Voice choice may change based on quality testing.

```bash
# Install
pip install opennarrator

# Download a voice (one-time)
opennarrator voices download --engine piper --voice en_US-libritts  # audiobook-trained, more natural

# Convert a book
opennarrator convert "The Great Gatsby.epub" \
  --voice en_US-libritts \
  --quality high \
  --speed 1.15 \
  --output gatsby.m4b

# That's it. Open in Apple Books and listen.
```

### Prerequisites

- **Python 3.12+**
- **ffmpeg** — `brew install ffmpeg` on macOS
- **A TTS engine** — Piper (CPU, fast), Kokoro (CPU, natural), or F5-TTS (GPU, best)

**Voice Quality:** We're testing multiple voices to find one suitable for long-form listening (5+ hours). See [Voice Quality Gate](docs/SPEC.md#voice-quality-gate) for criteria.

---

## 📁 Project Structure

```
opennarrator/
├── src/opennarrator/          # Python package
│   ├── cli/                   # Typer CLI (convert, voices, preview, server)
│   ├── pipeline/              # Core pipeline (extractor, synthesizer, packager)
│   ├── engines/               # Pluggable TTS engines (base, piper, kokoro, f5_tts)
│   ├── audio/                 # ffmpeg wrapper + loudness normalization
│   └── voice/                 # Voice manager, registry, cloning
├── docs/                      # Specs, architecture, engine comparison
├── spikes/                    # Feasibility experiments (Piper ⚠️, Kokoro 🔄)
├── tests/                     # unit/, integration/, smoke/, voice_quality/
├── webui/                     # Next.js frontend (Phase 2)
└── pyproject.toml
```

**Note:** Piper spike is technically validated (fast, clean API) but voice quality is unvalidated. See [Spike 001](spikes/001-piper-feasibility/README.md) for details.

---

## 🔬 Spike Results

| Spike | Engine | Verdict | Key Finding |
|-------|--------|---------|-------------|
| [001](spikes/001-piper-feasibility/README.md) | Piper | **PARTIAL** ✅⚠️ | **Technical ✅:** RTF 0.1x on Pi 5 (fast!), clean API, CPU-friendly. **Quality ⚠️:** `lessac` voice is robotic (failed quality gate). Testing `libritts` (audiobook-trained) next. |
| [002](spikes/002-kokoro-feasibility/) | Kokoro | 🔄 Pending | Blocked on Pi (Python 3.13 incompatibility). Testing on MacBook Neo next. Reportedly more natural than Piper. |

**Voice Quality Gate:** Before shipping v0.1, the chosen engine must pass a listening test: 2+ testers listen to a 5-minute sample and answer "Would you listen to a 10-hour book in this voice?" (≥50% must say "Yes"). See [Voice Quality Requirements](docs/SPEC.md#voice-quality-requirements).

---

## 🤝 Contributing

OpenNarrator is in active early development. The best way to contribute right now:

1. **Test voices** — Run the spikes on your hardware, report quality/speed
2. **Suggest engines** — Know of a great open-source TTS engine? Open an issue
3. **Share use cases** — What formats, voices, and features matter to you?

---

## 📜 License

MIT © 2026 [Sleuthy-Sloth](https://github.com/sleuthy-sloth)

OpenNarrator is free and open-source. The TTS engines it integrates with each carry their own licenses — check before commercial use.

---

<p align="center">
  <sub>Built with 🎙️ by <a href="https://github.com/sleuthy-sloth">Sleuthy-Sloth</a></sub>
</p>
