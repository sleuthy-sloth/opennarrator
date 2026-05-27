# OpenNarrator — MacBook Neo Handoff

**Date:** 2026-05-27
**GitHub:** [sleuthy-sloth/opennarrator](https://github.com/sleuthy-sloth/opennarrator) (private)
**Status:** Pre-alpha — engine spiking in progress

---

## Quick Start (Run on MacBook Neo)

```bash
# Clone the repo
git clone git@github.com:sleuthy-sloth/opennarrator.git
cd opennarrator

# Kokoro spike — test if voice quality beats Piper
mkdir -p spikes/002-kokoro-feasibility
cd spikes/002-kokoro-feasibility
python3 -m venv .venv
source .venv/bin/activate
pip install kokoro soundfile torch
python3 -c "import kokoro; print('Kokoro loaded:', dir(kokoro))"
```

Once Kokoro imports cleanly, I'll write the spike script to synthesize test samples and compare quality.

---

## What We Built So Far

### Spike 001 — Piper TTS (PARTIAL)
- **Speed:** RTF 0.1x on Pi 5 ARM. On A18 Pro: expect RTF < 0.05x
- **API:** Clean — `PiperVoice.load(model_path)` + `synthesize_wav(text, wave_file)`
- **API quirk:** `synthesize_wav` requires `wave.Wave_write` object, NOT raw file handle
  ```python
  import wave
  with wave.open("out.wav", "wb") as wav_file:
      voice.synthesize_wav(text, wav_file)
  ```
- **Voice quality:** `en_US-lessac` sounds robotic even with `length_scale`/`noise_scale` tuning
- **Untested:** `en_US-libritts` voice — trained on LibriTTS audiobook data, might sound more natural
- **Voice download:** `hf download rhasspy/piper-voices --include "en/en_US/lessac/*.onnx"`

### Spike 002 — Kokoro (BLOCKED on Pi)
- Requires Python < 3.13 (Pi has 3.13.5, `misaki` dependency incompatible)
- MacBook Neo likely has Python 3.12 → should work cleanly
- Needs PyTorch (CPU), transformers, scipy — all available via pip

---

## Architecture (Locked In)

| Decision | Choice |
|----------|--------|
| Language | Python 3.12+ |
| CLI | Typer + Rich |
| Config | Pydantic v2 |
| TTS interface | Abstract `BaseTTSEngine` — pluggable |
| Isolation | Subprocess per chapter (GPU memory safety) |
| Intermediates | Per-chapter WAV files (resume-after-failure) |
| Assembly | ffmpeg (concat + normalize + M4B packaging) |
| Input | EPUB (ebooklib), PDF (pymupdf), TXT (regex chapters) |
| License | MIT |
| Name | OpenNarrator |

---

## TTS Engine Strategy

| Priority | Engine | Why |
|----------|--------|-----|
| **Testing now** | Kokoro | Apache 2.0, CPU-friendly, reportedly more natural than Piper |
| **Fallback** | Piper `libritts` voice | Trained on audiobooks, same clean API, MIT |
| **Endgame** | F5-TTS | Best open-source quality, MIT, voice cloning — check CPU perf on A18 Pro |

---

## Implementation Plan (17 tasks, 5 phases)

1. **Phase 1: Skeleton** — Scaffolding, types, abstract engine interface + NullEngine, config
2. **Phase 2: Input** — EPUB/TXT extraction, chapter detection, text normalization
3. **Phase 3: TTS** — Engine adapter, voice manager, synthesizer with progress + resume
4. **Phase 4: Audio** — ffmpeg wrapper, loudness normalization (EBU R128), M4B packager
5. **Phase 5: CLI** — `opennarrator convert`, `opennarrator voices`, README, smoke test

Full plan at: [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)

---

## Key Files

```
opennarrator/
├── README.md                  # Beautiful project README with badges + roadmap
├── LICENSE                    # MIT
├── .gitignore                 # Excludes venvs, WAVs, models, caches
├── HANDOFF.md                 # This file
├── docs/
│   ├── SPEC.md                # Full specification
│   ├── IMPLEMENTATION_PLAN.md # Task breakdown
│   └── TTS_ENGINES.md         # Engine comparison table
└── spikes/
    └── 001-piper-feasibility/
        ├── README.md          # Spike verdict (PARTIAL)
        ├── spike.py           # Working Piper synthesis
        └── spike2_quality.py  # Quality tuning variants
```

---

## Known Gotchas

1. **Piper `synthesize_wav`:** Must pass `wave.Wave_write`, not raw `BufferedWriter`
2. **Kokoro + Python 3.13:** Doesn't work. Mac needs Python 3.12.
3. **Voice downloads:** Use `hf download rhasspy/piper-voices` for Piper, Kokoro has built-in download
4. **ffmpeg:** Not bundled. `brew install ffmpeg` required on macOS
5. **A18 Pro:** No MPS GPU. CPU-only for TTS inference. Piper RTF expected < 0.05x

---

## Next Action

1. Clone repo on MacBook Neo
2. Run Kokoro spike (`spikes/002-kokoro-feasibility/`)
3. If Kokoro voice quality passes → Kokoro becomes v0.1 engine
4. If not → test Piper `libritts` voice
5. If neither passes → F5-TTS (accept GPU requirement)
6. Once engine is chosen → kick off Phase 1 implementation
