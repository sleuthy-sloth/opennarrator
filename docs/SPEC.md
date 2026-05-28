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
| **TTS Engine (v0.1)** | Piper | latest | CPU-friendly, 50+ pre-trained voices, validates pipeline fast. RTF 0.1-0.2x on Pi 5 (spike validated). |
| **TTS Engine (v0.1 Alt)** | Kokoro | latest | Apache 2.0, reportedly more natural than Piper. Testing in progress. |
| **TTS Engine (v0.2)** | F5-TTS | latest | MIT license, state-of-the-art voice cloning, best open quality. GPU may be required (validate on A18 Pro). |
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

### Voice Quality Testing

Voice quality is the **#1 risk** for OpenNarrator. Automated tests verify technical correctness, but only human listening tests verify that the output is suitable for long-form listening (5+ hours).

#### Quality Gate Test (Manual, Required for v0.1)

**When:** Before committing to any TTS engine for v0.1 (Phase 0, Task 0.4)

**Methodology:**
1. Synthesize a 5-minute sample from a real book chapter (e.g., first chapter of Project Gutenberg's "Pride and Prejudice")
2. Recruit 2+ testers (developers, friends, family — anyone who listens to audiobooks)
3. Each tester listens to the full 5-minute sample
4. Answer one question: **"Would you listen to a 10-hour audiobook narrated in this voice?"** (Yes/No)
5. **Pass threshold:** ≥50% of testers say "Yes"

**Test Script:**
```bash
# Generate 5-minute sample
opennarrator preview pride_and_prejudice.epub --chapter 1 --voice <engine-voice> --output sample.wav

# Testers listen (headphones recommended)
# Answer: Would you listen to a 10-hour book in this voice? (Yes/No)

# Record results in tests/voice_quality/results/<engine>-<date>.md
```

**Why 5 minutes?** Long enough to detect robotic patterns, short enough that testers will actually complete it. 10+ minutes causes fatigue and reduces participation.

**Why ≥50% threshold?** Voice quality is subjective. If half the testers would listen for 10 hours, the voice is "good enough" for a significant audience. We're not competing with professional narrators — we're competing with no audiobook at all.

#### MOS (Mean Opinion Score) Testing (Optional, More Rigorous)

**When:** After quality gate passes, to compare engines objectively

**Methodology:**
1. Synthesize 10 samples (different sentences, varying length and complexity)
2. Recruit 5+ testers
3. Each tester rates each sample on a 1-5 scale:
   - **5 = Excellent** (professional narrator quality)
   - **4 = Good** (natural, pleasant, would listen for hours)
   - **3 = Fair** (acceptable, but robotic or unnatural in places)
   - **2 = Poor** (unpleasant, would not listen for more than a few minutes)
   - **1 = Bad** (unintelligible or extremely robotic)
4. Calculate average score across all testers and samples
5. **Target:** MOS ≥ 3.5 (between "Fair" and "Good")

**Test Script:**
```bash
# Generate 10 samples
python tests/voice_quality/generate_mos_samples.py --voice <engine-voice> --output samples/

# Testers rate each sample (web form or spreadsheet)
# Calculate MOS in tests/voice_quality/calculate_mos.py
```

**Why MOS?** Provides a quantitative metric for comparing engines. Useful for tracking quality improvements over time (e.g., when Kokoro releases a better model).

#### A/B Testing (Comparing Engines)

**When:** Choosing between two engines (e.g., Piper `libritts` vs Kokoro)

**Methodology:**
1. Synthesize the same 5-minute sample with both engines
2. Recruit 3+ testers
3. Each tester listens to both samples (randomized order to avoid bias)
4. Answer: **"Which voice would you prefer for a 10-hour audiobook?"** (A/B/No preference)
5. **Decision:** Choose the engine with ≥60% preference (or "No preference" if tied)

**Why A/B testing?** Removes absolute quality judgments ("Is this good enough?") and focuses on relative preference ("Which is better?"). More actionable for engine selection.

#### Performance Benchmarks (RTF Measurement)

**When:** After engine selection, to validate throughput

**Methodology:**
1. Synthesize a 10-minute sample (real book chapter)
2. Measure wall-clock time and audio duration
3. Calculate RTF (Real-Time Factor) = synthesis time / audio duration
4. **Target:** RTF < 0.5x (2x faster than real-time)

**Test Script:**
```python
# tests/voice_quality/benchmark_rtf.py
import time
from pathlib import Path
from opennarrator.engines import load_engine

engine = load_engine("piper")
voice = engine.get_voice("en_US-libritts")

text = Path("tests/fixtures/chapter_1.txt").read_text()
start = time.perf_counter()
engine.synthesize(text, voice, output_path="benchmark.wav")
elapsed = time.perf_counter() - start

# Get audio duration
import wave
with wave.open("benchmark.wav", "rb") as wf:
    audio_duration = wf.getnframes() / wf.getframerate()

rtf = elapsed / audio_duration
print(f"RTF: {rtf:.2f}x (target: < 0.5x)")
assert rtf < 0.5, f"RTF {rtf:.2f}x exceeds target"
```

**Why RTF < 0.5x?** A 10-hour audiobook should process in <5 hours. Slower than this makes batch conversion impractical (e.g., converting a library of 100 books).

#### Regression Tests (Automated)

**When:** After every engine update or model change

**Methodology:**
1. Maintain a "golden" set of 5 reference audio samples (known-good quality)
2. After engine update, synthesize the same samples with new engine version
3. Compare audio characteristics (not byte-for-byte, but perceptual similarity)
4. **Pass threshold:** Perceptual similarity > 80% (use PESQ or ViSQOL metrics)

**Why regression tests?** TTS engines update frequently. A new model version might be faster but sound worse. Regression tests catch quality degradation before it ships.

**Tools:**
- **PESQ** (Perceptual Evaluation of Speech Quality): ITU-T standard, requires license
- **ViSQOL** (Virtual Speech Quality Objective Listener): Google's open-source alternative
- **Simple approach:** Hash the audio waveform and alert if it changes significantly (crude but effective)

#### Voice Quality Test Fixtures

**Location:** `tests/voice_quality/fixtures/`

**Contents:**
- `pride_and_prejudice_ch1.txt` — First chapter of Jane Austen's "Pride and Prejudice" (public domain, ~2,500 words, 5-minute sample)
- `technical_text.txt` — Paragraph with numbers, abbreviations, and special characters (tests normalization)
- `dialogue.txt` — Conversation with quotes and em-dashes (tests prosody)
- `golden_samples/` — Reference audio files for regression testing (one per supported voice)

**Why these fixtures?** Cover the range of text types users will encounter: narrative prose, technical content, and dialogue. If the voice sounds good on all three, it's likely good enough for real books.

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
**Trade-off:** Voice cloning may require a GPU. CPU users get pre-trained voices only. **Risk:** F5-TTS CPU performance on MacBook Neo (A18 Pro, no MPS) is unvalidated — test early.

### Decision 6: Voice quality gate before v0.1 ship

**What:** Before committing to Piper (or any v0.1 engine), conduct a voice quality gate with explicit go/no-go criteria.
**Why:** Voice quality is the #1 risk. If the voice sounds robotic or unpleasant, users won't listen for hours, and the entire value proposition fails. We learned from Spike 001 that Piper's `en_US-lessac` voice sounds robotic even with tuning.
**How:**
1. Test `en_US-libritts` voice (trained on audiobook data, may sound more natural)
2. Test Kokoro on MacBook Neo (Apache 2.0, reportedly more natural)
3. If both fail quality gate → accept F5-TTS GPU requirement or pivot value proposition
4. Quality gate: 2+ testers listen to 5-minute sample, answer "Would you listen to a 10-hour book in this voice?" (yes/no)
**Trade-off:** Delays v0.1 by 1-2 weeks for voice testing. But shipping with bad voice quality is worse than delaying.

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
3. **Voice quality:** Generated audio is suitable for long-form listening (5+ hours). Measured via MOS (Mean Opinion Score) ≥ 3.5/5.0 on a 10-sample listening test, or subjective "would listen to a full book" assessment by 2+ testers.
4. **Three input formats:** EPUB, PDF, and TXT all produce usable output.
5. **Error recovery:** If synthesis fails on chapter 7 of 20, re-running the command skips chapters 1-6 and resumes from chapter 7.
6. **CPU-only support:** Runs on machines without NVIDIA GPUs (MacBook Neo A18 Pro, Raspberry Pi 5). RTF < 0.5x for acceptable throughput.
7. **Voice cloning (v0.2):** A 30-second voice sample produces a recognizable voice clone usable for full book narration.
8. **CLI UX:** Progress bars, ETA, and clear error messages. No silent failures.
9. **Documentation:** README with quickstart, voice quality guide, engine comparison, and FAQ.
10. **Test coverage:** ≥ 80% on pipeline modules.
11. **Single-command install:** `pip install opennarrator` followed by `opennarrator voices download` gets a working setup in under 5 minutes.

---

## Open Questions

*All questions resolved as of 2026-05-27. See Decisions Made below.*

---

## Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Name** | **OpenNarrator** | Clear, descriptive, available |
| **First TTS engine** | **Piper** (v0.1), then **F5-TTS** (v0.2) | Piper validates pipeline fast on CPU. F5-TTS adds quality + cloning later. **Voice quality gate required before v0.1 ship.** |
| **Voice sample length** | **30 seconds minimum** for cloning | F5-TTS papers show 15-30s viable. Longer = better quality. |
| **Distribution** | **pip install** for v0.1, `.app` bundle in v0.3 | Ship fast with pip. Bundle Python + ffmpeg for non-technical users later. |
| **Commercial intent** | **Pure open-source** (MIT) | No commercial offering planned. Revisit if traction justifies hosted API. |
| **Target OS** | **macOS first**, then Linux, then Windows | Primary dev machine is Mac. Linux similar. Windows follows. |
| **Cover art** | **Yes** — extract from EPUB, embed in M4B | Low effort, high polish. Users expect it. |
| **SSML support** | **Not in v0.1** — raw text only | Simpler. Add SSML in v0.2 if engines support it and quality improves. |

---

## Voice Quality Requirements

Voice quality is the **critical success factor** for OpenNarrator. Users will listen for hours — if the voice is robotic, unpleasant, or fatiguing, the tool fails regardless of technical correctness.

### Quality Gate Criteria

Before shipping v0.1, the chosen TTS engine must pass:

1. **Listening test:** 2+ testers listen to a 5-minute sample (1 chapter from a real book)
2. **Question:** "Would you listen to a 10-hour audiobook narrated in this voice?" (Yes/No)
3. **Pass threshold:** ≥ 50% of testers say "Yes"
4. **Alternative:** MOS (Mean Opinion Score) ≥ 3.5/5.0 on a 10-sample test (more rigorous, but requires more testers)

### Voice Candidates (v0.1)

| Voice | Engine | Status | Quality Notes |
|-------|--------|--------|---------------|
| `en_US-lessac` | Piper | ❌ Failed quality gate | Sounds robotic even with `length_scale`/`noise_scale` tuning |
| `en_US-libritts` | Piper | 🔄 Untested | Trained on LibriTTS audiobook data — may sound more natural |
| Kokoro default | Kokoro | 🔄 Testing | Apache 2.0, reportedly more natural than Piper. Blocked on Pi (Python 3.13), testing on MacBook Neo. |

### If Quality Gate Fails

If neither Piper `libritts` nor Kokoro passes the quality gate:

1. **Option A:** Accept F5-TTS as v0.1 engine (may require GPU, validate CPU performance on A18 Pro)
2. **Option B:** Pivot value proposition — position as "fast preview generation" not "audiobook production"
3. **Option C:** Defer v0.1 until a better CPU-friendly engine emerges (Kokoro improvements, new engines)

**Recommendation:** Test `libritts` and Kokoro first. If both fail, accept F5-TTS GPU requirement and document it clearly.
