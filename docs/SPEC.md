# Spec: OpenNarrator — Open-Source Audiobook Creator

**Version:** 0.1.0
**Status:** Draft — Awaiting Review
**Created:** 2026-05-27

---

## Objective

OpenNarrator is an open-source desktop application that converts ebooks (EPUB, PDF, TXT) into professional-quality audiobooks (M4B format) using open-source TTS engines. It breaks the ElevenLabs / commercial TTS stranglehold by combining state-of-the-art open voice models into a polished, user-friendly pipeline.

### Who is this for?

**Primary:** Self-hosters, power users, and accessibility advocates who want high-quality audiobook generation without per-character pricing or vendor lock-in.
**Secondary:** Non-technical users (via Web UI) who just want to upload a book and download an audiobook.

### What does success look like?

A user runs `opennarrator convert book.epub --voice my-voice` and gets a chaptered M4B file that sounds good enough to listen to for hours — no manual intervention, no API keys, no per-minute billing.

---

## Tech Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Language** | Python | 3.12+ | Best ML/TTS ecosystem. Every major open-source TTS engine has Python bindings. |
| **CLI Framework** | Typer + Rich | latest | Fast CLI building, beautiful progress bars and live displays. |
| **TTS Engine (Primary)** | F5-TTS | latest | MIT license, state-of-the-art voice cloning, best open quality as of 2026. |
| **TTS Engine (Fallback)** | Piper | latest | CPU-friendly, 50+ pre-trained voices, fast enough for real-time preview. |
| **TTS Engine (Alt)** | Kokoro | latest | Apache 2.0, emerging quality contender with small model size. |
| **Audio Processing** | ffmpeg (subprocess) | system | Industry standard. M4B packaging, normalization, silence trimming, chapter markers. |
| **EPUB Parsing** | ebooklib | latest | Pure Python EPUB2/EPUB3 reader with TOC + spine extraction. |
| **PDF Parsing** | pymupdf (fitz) | latest | Fastest Python PDF text extraction with layout preservation. |
| **Config/Validation** | Pydantic v2 | latest | Type-safe config, CLI arg validation, TTS engine settings schemas. |
| **Packaging** | PyInstaller or Nuitka | latest | Single-binary distribution for non-technical users. |
| **Web UI (Phase 2)** | FastAPI + Next.js 16 | latest | REST API for job management, React frontend for drag-and-drop UX. |
| **Testing** | pytest + pytest-cov | latest | Unit tests for pipeline stages, integration tests for end-to-end conversion. |

---

## Commands

```bash
# Development
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Core CLI
opennarrator convert book.epub --voice my-voice --output book.m4b
opennarrator convert book.pdf --voice default --speed 1.1 --output book.m4b
opennarrator convert book.txt --voice sample.wav --quality high

# Voice management
opennarrator voices list                         # List installed voices
opennarrator voices clone sample.wav --name "My Voice"  # Clone a voice
opennarrator voices download --engine piper --voice en_US-lessac  # Download pre-trained
opennarrator voices info my-voice                # Voice details

# Preview
opennarrator preview book.epub --chapter 3 --voice my-voice  # Generate 30s sample

# Job management (Web UI backend)
opennarrator server --port 8080                  # Start the API server
opennarrator jobs list                           # List conversion jobs
opennarrator jobs status <job-id>                # Check job progress

# Testing
pytest                                  # Run all tests
pytest --cov=opennarrator               # With coverage
pytest tests/unit/                      # Unit tests only
pytest tests/integration/               # Integration tests
pytest -m "slow"                        # Slow/long-running tests

# Linting
ruff check src/                         # Lint
ruff format src/                        # Format
mypy src/                               # Type check
```

---

## Project Structure

```
opennarrator/
├── src/
│   └── opennarrator/
│       ├── __init__.py
│       ├── __main__.py              # Entry point: python -m opennarrator
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py              # Typer app, top-level commands
│       │   ├── convert.py           # `opennarrator convert` command
│       │   ├── voices.py            # `opennarrator voices` subcommands
│       │   ├── preview.py           # `opennarrator preview` command
│       │   └── server.py            # `opennarrator server` command
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── extractor.py         # Extract text + structure from input formats
│       │   ├── segmenter.py         # Split into chapters/sections
│       │   ├── normalizer.py        # Text cleanup, SSML prep, number expansion
│       │   ├── synthesizer.py       # Orchestrate TTS engine per segment
│       │   └── packager.py          # Combine audio, add chapter markers, output M4B
│       ├── engines/
│       │   ├── __init__.py
│       │   ├── base.py              # Abstract TTS engine interface
│       │   ├── f5_tts.py            # F5-TTS engine adapter
│       │   ├── piper.py             # Piper engine adapter
│       │   └── kokoro.py            # Kokoro engine adapter
│       ├── audio/
│       │   ├── __init__.py
│       │   ├── processor.py         # Silence trimming, loudness normalization
│       │   └── ffmpeg.py            # ffmpeg subprocess wrapper
│       ├── voice/
│       │   ├── __init__.py
│       │   ├── manager.py           # Voice CRUD, file management
│       │   ├── cloner.py            # Voice cloning pipeline (F5-TTS)
│       │   └── registry.py          # Discover installed voices
│       ├── server/                   # Phase 2: FastAPI server
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── routes/
│       │   └── models/
│       ├── config.py                # Pydantic settings, config file management
│       ├── types.py                 # Shared types: Voice, Job, Chapter, Format
│       └── exceptions.py            # Custom exception hierarchy
├── tests/
│   ├── unit/
│   │   ├── test_extractor.py
│   │   ├── test_segmenter.py
│   │   ├── test_normalizer.py
│   │   ├── test_synthesizer.py
│   │   ├── test_packager.py
│   │   └── test_voice_manager.py
│   ├── integration/
│   │   ├── test_epub_to_m4b.py
│   │   ├── test_pdf_to_m4b.py
│   │   └── test_voice_cloning.py
│   ├── fixtures/
│   │   ├── sample.epub
│   │   ├── sample.pdf
│   │   ├── sample.txt
│   │   └── sample_voice.wav
│   └── conftest.py
├── webui/                            # Phase 2: Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   └── package.json
├── docs/
│   ├── SPEC.md                      # This file
│   ├── ARCHITECTURE.md              # Detailed architecture decisions
│   ├── TTS_ENGINES.md               # Comparison of supported engines
│   └── VOICE_CLONING.md             # Voice cloning guide
├── pyproject.toml                   # Dependencies, tool config
├── README.md
├── LICENSE                          # MIT
└── .gitignore
```

---

## Code Style

### Python conventions (example):

```python
"""Extract structured text content from ebook formats."""

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from opennarrator.exceptions import ExtractionError
from opennarrator.types import Chapter, BookMetadata


class Extractor(Protocol):
    """Protocol for format-specific text extractors."""

    def extract(self, path: Path) -> tuple[list[Chapter], BookMetadata]:
        """Extract chapters and metadata from the given file.

        Args:
            path: Path to the ebook file.

        Returns:
            Ordered list of Chapter objects and BookMetadata.

        Raises:
            ExtractionError: If the file is malformed or unreadable.
        """
        ...


class EpubExtractor:
    """Extract text from EPUB files using ebooklib."""

    def __init__(self, preserve_images: bool = False) -> None:
        self._preserve_images = preserve_images

    def extract(self, path: Path) -> tuple[list[Chapter], BookMetadata]:
        if not path.suffix.lower() == ".epub":
            raise ExtractionError(f"Expected .epub file, got {path.suffix}")

        # Extraction logic...
        ...


# Type-safe configuration
class SynthesizerConfig(BaseModel):
    engine: str = "f5_tts"
    voice: str = "default"
    speed: float = 1.0
    quality: str = "high"  # high | medium | low
    device: str = "auto"   # auto | cpu | cuda | mps
```

### Key conventions:
- **Naming:** snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants.
- **Type hints:** Required on all public functions and methods. mypy strict mode.
- **Docstrings:** Google-style for public API. No docstrings for obvious private methods.
- **Imports:** stdlib → third-party → local, each block sorted alphabetically.
- **Error handling:** Custom exception hierarchy. Never catch `Exception` bare. Always re-raise with context.
- **No wildcard imports.** `from module import *` is banned.
- **Line length:** 100 characters (matching Ruff default).
- **Async:** Use `asyncio` for the server layer only. Pipeline is synchronous (GPU-bound, not I/O-bound).

---

## Testing Strategy

| Level | Framework | Location | What it tests | Run time target |
|-------|-----------|----------|---------------|-----------------|
| **Unit** | pytest | `tests/unit/` | Individual functions, classes. TTS engines mocked. | < 30s total |
| **Integration** | pytest | `tests/integration/` | Pipeline stages end-to-end. Real ffmpeg, real Piper on CPU. Small test fixtures only. | < 5 min |
| **Smoke** | pytest | `tests/smoke/` | Full conversion with real TTS. Marked `@pytest.mark.slow`. Run on demand only. | 10+ min |
| **CLI** | pytest + CliRunner | inline with unit | CLI arg parsing, error messages, help text output. | < 5s |

### Coverage requirements:
- **Pipeline modules:** ≥ 90% line coverage. These are the critical path.
- **Engine adapters:** ≥ 80%. Heavy mocking of actual TTS inference.
- **CLI layer:** ≥ 70%. Focus on error paths and argument parsing.
- **Server (Phase 2):** ≥ 80%.

### Testing rules:
- Tests live in `tests/` mirroring `src/opennarrator/` structure.
- Test fixtures are small: sample EPUB = 3 chapters, sample PDF = 2 pages, sample voice = 10s WAV.
- Never call real TTS inference in unit tests — mock the engine.
- Integration tests may use Piper on CPU (fast enough) but never F5-TTS (needs GPU).
- `conftest.py` provides shared fixtures: `tmp_workspace`, `sample_epub`, `sample_voice`.

---

## Boundaries

### Always do:
- Run `ruff check && ruff format && mypy src/` before committing.
- Write tests before or alongside new pipeline code.
- Validate all user-provided paths and inputs at the CLI boundary.
- Use Pydantic models for all configuration (no raw dicts).
- Handle CTRL+C gracefully — clean up temp files, report partial progress.
- Log TTS progress so users know where they are in a 10-hour book.

### Ask first:
- Adding a new dependency (pip package).
- Changing the TTS engine interface (`engines/base.py`).
- Modifying the M4B packaging logic (easy to break chapter markers).
- Changing Python version requirement.
- Adding a new input format (EPUB/PDF/TXT are the core three).

### Never do:
- Commit API keys, tokens, or secrets.
- Bundle proprietary TTS models or voices (license violation risk).
- Ship ffmpeg binaries in the repo (system dependency).
- Hardcode paths that assume a specific OS or user directory.
- Call `os.system()` or `shell=True` — use `subprocess.run()` with argument lists.
- Block the main thread during TTS inference — always run in a subprocess or thread.

---

## Architecture Decisions

### Decision 1: CLI-first, Web UI as Phase 2

**What:** The MVP is a CLI tool. A FastAPI + Next.js web UI wraps it in Phase 2.
**Why:** The core value is the conversion pipeline. A CLI ships faster and serves power users immediately. The web UI is a UX layer on top of the same pipeline — no architecture changes needed.
**Trade-off:** Delays non-technical user adoption until Phase 2.

### Decision 2: Pluggable TTS engines via abstract base class

**What:** `engines/base.py` defines a `BaseTTSEngine` protocol. Each engine (F5-TTS, Piper, Kokoro) is an adapter.
**Why:** The TTS landscape changes fast. Six months from now, there might be a better engine. Swapping should require one new file, not a rewrite.
**Trade-off:** Slightly more abstraction overhead now, but prevents vendor lock-in to one TTS model.

### Decision 3: Subprocess isolation for TTS inference

**What:** Each TTS engine runs in its own subprocess, communicating via temporary WAV files.
**Why:** GPU memory leaks in ML libraries are common and hard to debug. Subprocess isolation guarantees memory is freed after each chapter. Also allows future distributed processing (multiple GPUs).
**Trade-off:** IPC overhead. For Piper on CPU this is negligible. For F5-TTS the model load time dominates anyway.

### Decision 4: WAV intermediates, ffmpeg for final assembly

**What:** TTS engines output per-chapter WAV files. ffmpeg concatenates, normalizes, and packages into M4B.
**Why:** WAV is lossless, universally supported, and simple. Per-chapter files enable resume-after-failure (don't re-synthesize chapters that succeeded). ffmpeg is the gold standard for audio processing.
**Trade-off:** Disk usage during conversion (book-length WAV ≈ 500MB-1GB). Acceptable for a desktop tool.

### Decision 5: Voice cloning via F5-TTS only

**What:** Voice cloning is supported exclusively through F5-TTS (the only open-source engine with reliable cloning as of 2026).
**Why:** Piper and Kokoro are multi-speaker but don't do cloning. XTTSv2 does but has licensing restrictions. F5-TTS is MIT-licensed and produces the best clones.
**Trade-off:** Voice cloning requires a GPU. CPU users get pre-trained voices only.

---

## Data Flow

```
Input File (EPUB/PDF/TXT)
        │
        ▼
   Extractor ────► Chapters[] + Metadata
        │              │
        │              ▼
        │         Segmenter ────► Chapter chunks (text + index)
        │              │
        │              ▼
        │         Normalizer ────► Cleaned text, SSML annotations
        │              │
        │              ▼
        │    ┌── Synthesizer ────► Per-chapter WAV files
        │    │       │
        │    │       ├── TTS Engine (F5-TTS / Piper / Kokoro)
        │    │       └── Voice Registry
        │    │
        │    └──► Packager
        │              │
        │              ├── ffmpeg concat (WAV → single audio)
        │              ├── loudnorm normalization
        │              ├── silence trimming
        │              └── M4B container + chapter markers + metadata
        │                     │
        ▼                     ▼
   Output: book.m4b (with embedded chapters, cover art, metadata)
```

---

## Success Criteria

1. **Core conversion:** `opennarrator convert book.epub --voice default` produces a playable M4B file with correct chapter markers.
2. **Voice consistency:** A single voice is used consistently across all chapters (no voice drift).
3. **Three input formats:** EPUB, PDF, and TXT all produce usable output.
4. **Error recovery:** If synthesis fails on chapter 7 of 20, re-running the command skips chapters 1-6 and resumes from chapter 7.
5. **GPU and CPU support:** Runs on machines with and without NVIDIA GPUs. GPU gets F5-TTS quality. CPU gets Piper quality.
6. **Voice cloning:** A 30-second voice sample produces a recognizable voice clone usable for full book narration.
7. **CLI UX:** Progress bars, ETA, and clear error messages. No silent failures.
8. **Documentation:** README with quickstart, voice cloning guide, engine comparison, and FAQ.
9. **Test coverage:** ≥ 80% on pipeline modules.
10. **Single-command install:** `pip install opennarrator` followed by `opennarrator voices download` gets a working setup in under 5 minutes.

---

## Open Questions

1. **Name: OpenNarrator?** Alternatives: AudiobookForge, LibroVox (taken?), OpenAudiobook, VoxForge. Settle before first commit.
2. **First TTS engine to implement:** F5-TTS for quality, or Piper for speed + CPU support? Recommendation: Piper first (fast, works everywhere, validates the pipeline), then F5-TTS for quality.
3. **Minimum voice sample length for cloning:** 30 seconds? 60 seconds? F5-TTS papers suggest 15-30s is viable but longer = better. Need to experiment.
4. **Distribution strategy:** PyPI package only, or also a single binary (PyInstaller/Nuitka) for non-technical users? The binary would bundle Python + ffmpeg.
5. **Commercial use:** MIT license allows it. Is the goal purely open-source, or a future commercial offering (hosted API, premium voices)?
6. **Mac vs. Linux vs. Windows:** Which OS first? You're on Mac. Priority should be macOS + Linux. Windows support can follow.
7. **Cover art extraction:** Should we extract cover art from EPUB and embed it in the M4B? Low effort, high polish.
8. **SSML support:** Do we generate SSML (pauses, emphasis) from punctuation/prose, or feed raw text to the TTS engine? Raw text is simpler. SSML could improve quality for specific engines that support it.
