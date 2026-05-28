# Implementation Plan: OpenNarrator v0.1.0 — Piper Engine MVP

**Spec:** `docs/SPEC.md`
**Target:** macOS-first CLI that converts EPUB/TXT → M4B using Piper TTS
**Status:** Phase 0 in progress — libritts tested, awaiting quality gate decision

---

## Overview

Build the core audiobook pipeline with a **quality-validated TTS engine** (Piper, Kokoro, or F5-TTS — see Phase 0). The goal is a working `opennarrator convert book.epub --voice <engine-specific>` command that produces a playable M4B file with chapter markers **and voice quality suitable for long-form listening**. No GPU required (unless F5-TTS is chosen). No voice cloning yet. Just the pipeline working end-to-end with acceptable voice quality.

---

## Architecture Decisions (Carried Forward from Spec)

- **CLI-first:** Typer + Rich for beautiful terminal UX
- **Pluggable engines:** Abstract base class from day one — Piper is just the first adapter
- **Subprocess isolation:** Each chapter synthesis runs in a subprocess
- **WAV intermediates:** Per-chapter WAV files enable resume-after-failure
- **ffmpeg assembly:** Concatenation, normalization, M4B packaging

---

## Phased Implementation

### Phase 0: Engine Selection & Voice Quality Gate (CRITICAL)

**Goal:** Resolve the voice quality question before committing to implementation. This is the #1 risk — if we ship with robotic-sounding voices, the tool fails regardless of technical quality.

**Status:** IN PROGRESS (Task 0.1 complete, awaiting quality gate assessment)

- [x] Task 0.1: Test Piper `en_US-libritts` voice ✅
  - **What:** Download and test the `en_US-libritts` voice (trained on LibriTTS audiobook data)
  - **Why:** `lessac` failed quality gate (robotic). `libritts` may sound more natural.
  - **How:**
    ```bash
    hf download rhasspy/piper-voices --include "en/en_US/libritts/*.onnx"
    # Synthesize 5-minute sample from a real book chapter
    # 2+ testers listen and answer: "Would you listen to a 10-hour book in this voice?"
    ```
  - **Acceptance:** ≥ 50% of testers say "Yes" → Piper validated. Otherwise → proceed to Task 0.2.
  - **Files:** `spikes/001-piper-feasibility/spike3_libritts.py`
  
  **Results (2026-05-27):**
  - **Model:** `en_US-libritts-high` (137 MB)
  - **RTF:** 0.48x on Apple Silicon arm64 (2x faster than real-time)
  - **Load time:** 0.3-0.4s
  - **Projection:** 10-hour book in ~4.8 hours
  - **Sample:** `spikes/001-piper-feasibility/output-libritts/libritts_quality_test.wav` (2.1 min, 5.3 MB)
  - **Quality gate:** AWAITING ASSESSMENT — user must listen and answer: "Would you listen to a 10-hour book in this voice?"

- [ ] Task 0.2: Test Kokoro on MacBook Neo
  - **What:** Set up Kokoro TTS on MacBook Neo (Python 3.12, no 3.13 incompatibility)
  - **Why:** Kokoro (Apache 2.0) reportedly sounds more natural than Piper. Blocked on Pi (Python 3.13), but should work on Mac.
  - **How:**
    ```bash
    cd spikes/002-kokoro-feasibility
    python3 -m venv .venv && source .venv/bin/activate
    pip install kokoro soundfile torch
    # Synthesize same 5-minute sample
    # Same listening test as Task 0.1
    ```
  - **Acceptance:** ≥ 50% of testers say "Yes" → Kokoro becomes v0.1 engine. Otherwise → proceed to Task 0.3.
  - **Files:** `spikes/002-kokoro-feasibility/README.md`, `spike.py`

- [ ] Task 0.3: Validate F5-TTS CPU performance on MacBook Neo
  - **What:** Test if F5-TTS runs acceptably on A18 Pro CPU (no MPS GPU)
  - **Why:** If Piper and Kokoro both fail quality gate, F5-TTS is the fallback. But it may require GPU.
  - **How:**
    ```bash
    pip install f5-tts
    # Synthesize 1-minute sample, measure RTF
    # RTF < 0.5x = acceptable, RTF > 1.0x = too slow
    ```
  - **Acceptance:** RTF < 0.5x → F5-TTS viable on CPU. Otherwise → pivot or defer.
  - **Files:** `spikes/003-f5-tts-cpu-performance/README.md`

- [ ] Task 0.4: Make final engine decision
  - **Decision tree:**
    - Piper `libritts` passes quality gate → **Piper is v0.1 engine**
    - Kokoro passes quality gate → **Kokoro is v0.1 engine**
    - F5-TTS CPU performance acceptable → **F5-TTS is v0.1 engine (document GPU recommendation)**
    - All fail → **Pivot value proposition** (fast preview generation, not audiobook production) or **defer v0.1**
  - **Deliverable:** Update SPEC.md and IMPLEMENTATION_PLAN.md with final engine choice

**Checkpoint: Engine Selected**
- [ ] Voice quality gate passed (2+ testers approve)
- [ ] Engine choice documented in SPEC.md
- [ ] Ready to proceed to Phase 1

---

### Phase 1: Skeleton & Pipeline Contracts (Foundation)

**Goal:** Project scaffolding, abstract interfaces, and a "null" engine that outputs silence. Validates the pipeline architecture without any real TTS dependency.

- [ ] Task 1: Project scaffolding
  - Acceptance: `pyproject.toml`, `src/opennarrator/`, `tests/`, venv setup. `pip install -e ".[dev]"` works. Ruff + mypy configured.
  - Verify: `ruff check src/ && mypy src/ && pytest` all pass (0 tests initially)
  - Files: `pyproject.toml`, `src/opennarrator/__init__.py`, `src/opennarrator/__main__.py`, `.gitignore`
  
  **pyproject.toml Requirements:**
  ```toml
  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [project]
  name = "opennarrator"
  version = "0.1.0"
  description = "Open-source audiobook creator — convert ebooks to M4B using open-source TTS engines"
  readme = "README.md"
  requires-python = ">=3.12"
  license = {text = "MIT"}
  authors = [
    {name = "Sleuthy-Sloth", email = "your-email@example.com"}
  ]
  dependencies = [
    "typer[all]>=0.12.0",           # CLI framework with Rich integration
    "rich>=13.7.0",                 # Beautiful terminal output
    "pydantic>=2.6.0",              # Config validation and type safety
    "pydantic-settings>=2.1.0",     # Settings management from env/files
    "ebooklib>=0.18",               # EPUB parsing
    "pymupdf>=1.24.0",              # PDF parsing (fitz)
    "huggingface-hub>=0.22.0",      # Voice model downloads
  ]

  [project.optional-dependencies]
  dev = [
    "pytest>=8.1.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "types-setuptools",             # Type stubs
  ]
  piper = [
    "piper-tts>=1.2.0",             # Piper TTS engine (optional, install separately)
  ]

  [project.scripts]
  opennarrator = "opennarrator.cli.main:app"

  [tool.hatch.build.targets.wheel]
  packages = ["src/opennarrator"]

  [tool.ruff]
  line-length = 100
  target-version = "py312"
  select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "SIM",    # flake8-simplify
  ]
  ignore = [
    "E501",   # Line too long (handled by formatter)
  ]

  [tool.ruff.format]
  quote-style = "double"
  indent-style = "space"

  [tool.mypy]
  python_version = "3.12"
  strict = true
  warn_return_any = true
  warn_unused_configs = true
  disallow_untyped_defs = true
  disallow_incomplete_defs = true
  check_untyped_defs = true
  no_implicit_optional = true
  warn_redundant_casts = true
  warn_unused_ignores = true
  warn_no_return = true
  strict_equality = true

  [[tool.mypy.overrides]]
  module = ["ebooklib.*", "pymupdf.*"]
  ignore_missing_imports = true

  [tool.pytest.ini_options]
  testpaths = ["tests"]
  python_files = ["test_*.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]
  addopts = "-v --tb=short"
  markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests requiring external dependencies",
  ]
  ```
  
  **Directory Structure:**
  ```
  opennarrator/
  ├── src/
  │   └── opennarrator/
  │       ├── __init__.py          # Package version: __version__ = "0.1.0"
  │       ├── __main__.py          # Entry point: from opennarrator.cli.main import app; app()
  │       ├── cli/                 # Typer CLI commands
  │       ├── pipeline/            # Extractor, synthesizer, packager
  │       ├── engines/             # TTS engine adapters
  │       ├── audio/               # ffmpeg wrapper, normalization
  │       └── voice/               # Voice manager, registry
  ├── tests/
  │   ├── unit/
  │   ├── integration/
  │   ├── smoke/
  │   ├── voice_quality/           # Listening tests, MOS, benchmarks
  │   ├── fixtures/
  │   └── conftest.py
  ├── docs/
  ├── spikes/
  ├── pyproject.toml
  ├── README.md
  ├── LICENSE
  └── .gitignore
  ```
  
  **Setup Commands:**
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -e ".[dev]"
  
  # Verify setup
  ruff check src/          # Should pass (0 errors)
  mypy src/                # Should pass (0 errors)
  pytest                   # Should pass (0 tests, no failures)
  opennarrator --help      # Should show CLI help (empty, but works)
  ```

- [ ] Task 2: Core types and exceptions
  - Acceptance: `Chapter`, `BookMetadata`, `Voice`, `ConversionJob` types defined. Exception hierarchy: `OpenNarratorError`, `ExtractionError`, `SynthesisError`, `PackagingError`.
  - Verify: Types import cleanly, exceptions have useful messages
  - Files: `src/opennarrator/types.py`, `src/opennarrator/exceptions.py`

- [ ] Task 3: Abstract engine interface + NullEngine
  - Acceptance: `BaseTTSEngine` ABC with `synthesize(text, voice, output_path) -> Path` and `list_voices() -> list[Voice]`. `NullEngine` outputs 1 second of silence per chapter.
  - Verify: `pytest tests/unit/test_null_engine.py` — confirm WAV file creation
  - Files: `src/opennarrator/engines/base.py`, `src/opennarrator/engines/null_engine.py`

- [ ] Task 4: Config system
  - Acceptance: Pydantic `Settings` model loaded from `~/.config/opennarrator/config.yaml` with defaults. CLI overrides via env vars.
  - Verify: Unit tests for config loading, env var override, invalid config rejection
  - Files: `src/opennarrator/config.py`

### Checkpoint: Foundation
- [x] Project installs cleanly
- [x] Types and interfaces defined
- [x] NullEngine proves the pipeline contract works
- [x] Config system loads/saves correctly

---

### Phase 2: Input Pipeline (Text Extraction)

**Goal:** Extract structured text from EPUB and TXT files. Chapters detected, text cleaned, ready for synthesis.

- [ ] Task 5: EPUB extractor
  - Acceptance: `EpubExtractor.extract(path)` returns `list[Chapter]` with titles and body text from a real EPUB3 file. Handles nested TOC, inline HTML stripping, and missing titles gracefully.
  - Verify: Unit test with 3-chapter test fixture EPUB. Integration test with a real public-domain EPUB (e.g., Project Gutenberg).
  - Files: `src/opennarrator/pipeline/extractor.py` (EpubExtractor class)

- [ ] Task 6: TXT extractor with chapter detection
  - Acceptance: `TxtExtractor.extract(path)` detects chapters via regex patterns (`Chapter 1`, `CHAPTER I`, `1.`, etc.) and splits accordingly. Falls back to "whole book as one chapter" if no patterns found.
  - Verify: Unit tests with various chapter heading styles. Test with raw text without chapters (one-chapter fallback).
  - Files: `src/opennarrator/pipeline/extractor.py` (TxtExtractor class)

- [ ] Task 7: Text normalizer
  - Acceptance: Expands numbers ("42" → "forty two"), normalizes whitespace, strips HTML entities, handles quotes and em-dashes. Output is clean speakable text.
  - Verify: Unit tests for number expansion, entity stripping, whitespace normalization
  - Files: `src/opennarrator/pipeline/normalizer.py`

### Checkpoint: Input Pipeline
- [x] EPUB and TXT both produce clean Chapter objects
- [x] Text is normalized and speakable
- [x] All unit tests pass

---

### Phase 3: Piper TTS Integration

**Goal:** Real speech synthesis using Piper. This is the heart of v0.1.

- [ ] Task 8: Piper engine adapter
  - Acceptance: `PiperEngine` implements `BaseTTSEngine`. `synthesize(text, voice, output_path)` calls Piper subprocess, produces a WAV file. `list_voices()` returns available Piper voices. Handles Piper not installed gracefully.
  - Verify: Unit tests with mocked subprocess. Integration test with real Piper + `en_US-lessac` voice on a single sentence.
  - Files: `src/opennarrator/engines/piper.py`

- [ ] Task 9: Voice manager
  - Acceptance: `VoiceManager` discovers installed Piper voices, tracks user-cloned voices, provides `get_voice(name) -> Voice`. Handles Piper voice download guidance.
  - Verify: Unit tests for voice discovery from Piper models directory, error on missing voice
  - Files: `src/opennarrator/voice/manager.py`, `src/opennarrator/voice/registry.py`

- [ ] Task 10: Synthesizer pipeline stage
  - Acceptance: `Synthesizer.synthesize_chapters(chapters, engine, voice)` iterates chapters, calls engine per chapter, saves per-chapter WAVs. Reports progress with Rich. Supports resume (skip existing WAVs).
  - Verify: Integration test with NullEngine (fast). Unit test for resume logic.
  - Files: `src/opennarrator/pipeline/synthesizer.py`

### Checkpoint: TTS Working
- [x] Piper produces real speech from text
- [x] Multi-chapter synthesis with progress and resume
- [x] Voice discovery works

---

### Phase 4: Audio Assembly

**Goal:** Combine chapter WAVs into a final M4B file with chapter markers and metadata.

- [ ] Task 11: ffmpeg wrapper
  - Acceptance: `FFmpeg.concat_wavs(wav_paths, output_path)` concatenates WAV files. `FFmpeg.to_m4b(audio_path, chapters, metadata, output_path)` creates M4B with chapter markers, cover art, and metadata tags. Handles ffmpeg not installed.
  - Verify: Unit tests for command construction. Integration test with pre-made WAV files.
  - Files: `src/opennarrator/audio/ffmpeg.py`

- [ ] Task 12: Audio processor (loudness normalization)
  - Acceptance: Normalizes all chapter WAVs to consistent loudness (EBU R128 via ffmpeg loudnorm) before concatenation. Trims leading/trailing silence.
  - Verify: Integration test — verify output loudness is consistent across chapters
  - Files: `src/opennarrator/audio/processor.py`

- [ ] Task 13: M4B packager
  - Acceptance: `Packager.package(chapter_wavs, chapters, metadata, output_path)` runs the full assembly: normalize → concat → M4B with chapters. Output is a valid M4B file playable in Apple Books.
  - Verify: Integration test with NullEngine output. Manual verification: open M4B in Apple Books, confirm chapter navigation works.
  - Files: `src/opennarrator/pipeline/packager.py`

### Checkpoint: M4B Output
- [x] End-to-end pipeline produces a valid M4B
- [x] Chapter markers work in Apple Books
- [x] Audio loudness is consistent

---

### Phase 5: CLI & Polish

**Goal:** The `opennarrator` command is usable, helpful, and looks professional.

- [ ] Task 14: CLI — `convert` command
  - Acceptance: `opennarrator convert book.epub --voice en_US-lessac --output book.m4b` runs the full pipeline with Rich progress bars, ETA, and per-chapter status. Handles CTRL+C with cleanup. Exit codes: 0 success, 1 error.
  - Verify: Manual end-to-end run with a real EPUB. Test with --help output.
  - Files: `src/opennarrator/cli/main.py`, `src/opennarrator/cli/convert.py`

- [ ] Task 15: CLI — `voices` command
  - Acceptance: `opennarrator voices list` shows available Piper voices with language/quality info. `opennarrator voices download` shows Piper installation instructions.
  - Verify: Test voice list output format. Test with no Piper installed (useful error).
  - Files: `src/opennarrator/cli/voices.py`

- [ ] Task 16: README and quickstart docs
  - Acceptance: README with: project description, install instructions, Piper setup, quickstart example, engine comparison, FAQ. Links to full docs.
  - Verify: Human review
  - Files: `README.md`, `docs/QUICKSTART.md`

- [ ] Task 17: End-to-end smoke test
  - Acceptance: Full test: download a public-domain EPUB, run `opennarrator convert`, verify the M4B plays with chapters. Marked `@pytest.mark.slow`.
  - Verify: `pytest tests/smoke/test_epub_to_m4b.py -m slow`
  - Files: `tests/smoke/test_epub_to_m4b.py`

### Checkpoint: v0.1.0 Complete
- [x] `pip install opennarrator` → working audiobook conversion
- [x] CLI is polished with progress, ETA, error handling
- [x] README makes it easy to get started
- [x] All tests pass (unit + integration + smoke)

---

## Risks and Mitigations

### Critical Risks (Block v0.1)

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Voice quality fails quality gate** | **BLOCKER** — tool unusable for long-form listening | **HIGH** (Piper `lessac` already failed) | Test `en_US-libritts` (audiobook-trained). If fails → test Kokoro. If both fail → accept F5-TTS GPU requirement or pivot value proposition. See Phase 0. |
| **MacBook Neo has no MPS GPU** | **HIGH** — F5-TTS may be too slow on CPU | **MEDIUM** (untested) | Validate F5-TTS CPU performance early (Task 0.3). RTF < 0.5x = acceptable. If too slow → document GPU requirement clearly or defer F5-TTS to v0.2. |
| **Kokoro blocked on Python 3.13** | **MEDIUM** — can't test on Pi 5 | **CONFIRMED** (misaki dependency incompatible) | Test on MacBook Neo (likely Python 3.12). If MacBook Neo also has 3.13 → use pyenv to install 3.12. |

### Technical Risks (Manageable)

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Piper subprocess interface changes | Medium — breaks engine adapter | Low | Pin Piper version in `pyproject.toml`. Engine adapter catches subprocess errors with useful messages. Add integration test that runs real Piper. |
| ffmpeg not installed by default on macOS | High — blocks M4B output | High | Detect at CLI startup, show `brew install ffmpeg` guidance with exact command. Consider bundling ffmpeg in future binary distribution (v0.3). |
| EPUB structure varies wildly between publishers | Medium — extraction misses chapters | High | Start with well-structured EPUBs (Project Gutenberg). Add fallback regex chapter detection from TXT extractor. Log warnings when TOC is missing. |
| Voice consistency across long texts | Low for Piper (single-speaker models) | Low | Piper voices are deterministic per-model. Not a concern until F5-TTS voice cloning phase. Monitor for voice drift in 10+ hour books. |
| Large books exhaust disk space (WAV intermediates) | Low — 1GB for a long book | Medium | Warn if disk space < 2x estimated output size. Clean up WAVs on successful M4B creation. Add `--keep-wavs` flag for debugging. |

### Strategic Risks (Product-Market Fit)

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Voice quality never reaches "good enough"** | **BLOCKER** — entire value proposition fails | **MEDIUM** (Piper `lessac` failed, `libritts` and Kokoro untested) | Define "good enough" explicitly (quality gate). If no CPU-friendly engine passes → pivot to "fast preview generation" or accept GPU requirement. |
| **Users expect ElevenLabs quality** | High — negative reviews, low adoption | High | Set expectations clearly in README: "Open-source TTS quality, not ElevenLabs quality." Emphasize cost savings and privacy. Position as "good enough for most use cases." |
| **TTS engine landscape changes fast** | Medium — chosen engine becomes obsolete | Medium | Pluggable architecture (BaseTTSEngine) makes swapping engines a one-file change. Monitor new engines quarterly. |

### Risk Response Plan

**If voice quality gate fails for all CPU-friendly engines:**

1. **Option A: Accept GPU requirement**
   - Document clearly: "F5-TTS requires NVIDIA GPU (CUDA) for acceptable performance"
   - Provide cloud GPU option (user provides API key for remote inference)
   - Target audience: users with gaming PCs or cloud access

2. **Option B: Pivot value proposition**
   - Position as "fast preview generation" not "audiobook production"
   - Use case: "Preview a book before buying the professional audiobook"
   - Lower quality expectations, faster iteration

3. **Option C: Defer v0.1**
   - Wait for better CPU-friendly engines (Kokoro improvements, new models)
   - Monitor TTS research for breakthroughs
   - Risk: lose momentum, competitors ship first

**Recommendation:** Test `libritts` and Kokoro first. If both fail → Option A (accept GPU requirement) with clear documentation.

---

## Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| First TTS engine | **Piper** — CPU-friendly, validates pipeline fast |
| Target OS | **macOS first**, Linux and Windows follow |
| Name | **OpenNarrator** |
| Distribution | **pip install** for v0.1. `.app` bundle with Web UI in Phase 2 |
| Cover art extraction | **Yes** — extract from EPUB, embed in M4B |
| SSML support | **Not in v0.1** — raw text only |
| Voice sample length | **30 seconds minimum** for cloning (Phase 2 with F5-TTS) |
| Commercial intent | **Pure open-source** (MIT). Revisit if traction justifies hosted offering |
