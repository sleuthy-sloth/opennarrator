# Implementation Plan: OpenNarrator v0.1.0 — Piper Engine MVP

**Spec:** `docs/SPEC.md`
**Target:** macOS-first CLI that converts EPUB/TXT → M4B using Piper TTS
**Status:** Ready for implementation

---

## Overview

Build the core audiobook pipeline with Piper as the first TTS engine. The goal is a working `opennarrator convert book.epub --voice en_US-lessac` command that produces a playable M4B file with chapter markers. No GPU required. No voice cloning yet. Just the pipeline working end-to-end.

---

## Architecture Decisions (Carried Forward from Spec)

- **CLI-first:** Typer + Rich for beautiful terminal UX
- **Pluggable engines:** Abstract base class from day one — Piper is just the first adapter
- **Subprocess isolation:** Each chapter synthesis runs in a subprocess
- **WAV intermediates:** Per-chapter WAV files enable resume-after-failure
- **ffmpeg assembly:** Concatenation, normalization, M4B packaging

---

## Phased Implementation

### Phase 1: Skeleton & Pipeline Contracts (Foundation)

**Goal:** Project scaffolding, abstract interfaces, and a "null" engine that outputs silence. Validates the pipeline architecture without any real TTS dependency.

- [ ] Task 1: Project scaffolding
  - Acceptance: `pyproject.toml`, `src/opennarrator/`, `tests/`, venv setup. `pip install -e ".[dev]"` works. Ruff + mypy configured.
  - Verify: `ruff check src/ && mypy src/ && pytest` all pass (0 tests initially)
  - Files: `pyproject.toml`, `src/opennarrator/__init__.py`, `src/opennarrator/__main__.py`, `.gitignore`

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

| Risk | Impact | Mitigation |
|------|--------|------------|
| Piper subprocess interface changes | Medium — breaks engine adapter | Pin Piper version in docs. Engine adapter catches subprocess errors with useful messages. |
| ffmpeg not installed by default on macOS | High — blocks M4B output | Detect at CLI startup, show `brew install ffmpeg` guidance. Consider bundling ffmpeg in future binary distribution. |
| EPUB structure varies wildly between publishers | Medium — extraction misses chapters | Start with well-structured EPUBs. Add fallback regex chapter detection from TXT extractor. |
| Voice consistency across long texts | Low for Piper (single-speaker models) | Piper voices are deterministic per-model. Not a concern until F5-TTS voice cloning phase. |
| Large books exhaust disk space (WAV intermediates) | Low — 1GB for a long book | Warn if disk space < 2x estimated output size. Clean up WAVs on successful M4B creation. |

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
