# OpenNarrator — MacBook Neo Handoff

**Date:** 2026-05-27
**GitHub:** [sleuthy-sloth/opennarrator](https://github.com/sleuthy-sloth/opennarrator) (private)
**Status:** Phase 0 — Task 0.1 complete (libritts tested), awaiting quality gate assessment
**Last action:** Piper `en_US-libritts` synthesis works on arm64 Mac. 2.1-min sample generated. RTF 0.48x. User needs to listen and answer quality gate question.

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

### Spike 001 — Piper TTS (PARTIAL — Technical ✅, Quality ⚠️)
- **Speed:** RTF 0.1x on Pi 5 ARM. On A18 Pro: expect RTF < 0.05x ✅
- **API:** Clean — `PiperVoice.load(model_path)` + `synthesize_wav(text, wave_file)` ✅
- **API quirk:** `synthesize_wav` requires `wave.Wave_write` object, NOT raw file handle
  ```python
  import wave
  with wave.open("out.wav", "wb") as wav_file:
      voice.synthesize_wav(text, wav_file)
  ```
- **Voice quality:** `en_US-lessac` sounds robotic even with `length_scale`/`noise_scale` tuning ❌
  - **Failed quality gate:** Testers would not listen to a 10-hour book in this voice
  - **Next step:** Test `en_US-libritts` (audiobook-trained, may sound more natural)
- **Untested:** `en_US-libritts` voice — trained on LibriTTS audiobook data, might sound more natural
- **Voice download:** `hf download rhasspy/piper-voices --include "en/en_US/lessac/*.onnx"`

### Spike 002 — Kokoro (BLOCKED on Pi, PENDING on MacBook Neo)
- Requires Python < 3.13 (Pi has 3.13.5, `misaki` dependency incompatible) ❌
- MacBook Neo likely has Python 3.12 → should work cleanly (UNVALIDATED)
- Needs PyTorch (CPU), transformers, scipy — all available via pip
- **Priority:** Test this NEXT on MacBook Neo — reportedly more natural than Piper

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
5. **MacBook Neo A18 Pro — CRITICAL CONSTRAINT:**
   - **No MPS GPU** — CPU-only for all TTS inference
   - **F5-TTS risk:** May require GPU for acceptable performance. Test early (Task 0.3).
   - **Piper/Kokoro:** Should work fine on CPU. Piper RTF expected < 0.05x.
   - **Impact:** If F5-TTS is too slow on CPU, we either:
     - Accept GPU requirement (document clearly, users need NVIDIA GPU)
     - Pivot value proposition (fast preview, not audiobook production)
     - Defer v0.1 until better CPU-friendly engine emerges
6. **Voice quality is the #1 risk:** `lessac` failed quality gate. Must test `libritts` and Kokoro before committing to v0.1 engine.

---

## Next Action (PRIORITY ORDER)

**Phase 0: Engine Selection & Voice Quality Gate (IN PROGRESS)**

1. ✅ **Test Piper `en_US-libritts` voice** (Task 0.1 — COMPLETE)
   - Model: `en_US-libritts-high` (137 MB)
   - RTF: 0.48x (10h book in ~4.8h)
   - Sample: `spikes/001-piper-feasibility/output-libritts/libritts_quality_test.wav` (2.1 min)
   - **WAITING:** Listen to sample and answer quality gate question
   - If "Yes" → **Piper validated, proceed to Phase 1**

2. **If `libritts` fails → Test Kokoro on MacBook Neo** (Task 0.2)
   - Set up: `cd spikes/002-kokoro-feasibility && python3 -m venv .venv && source .venv/bin/activate`
   - Note: Kokoro requires Python 3.12 (NOT 3.13). Use `python3.12` or pyenv.
   - Install: `pip install kokoro soundfile torch`
   - Synthesize same 5-minute sample
   - Same listening test
   - If ≥50% say "Yes" → **Kokoro becomes v0.1 engine**

3. **If Kokoro fails → Validate F5-TTS CPU performance** (Task 0.3)
   - Test if F5-TTS runs acceptably on A18 Pro CPU (no MPS)
   - RTF < 0.5x = acceptable, RTF > 1.0x = too slow
   - If acceptable → **F5-TTS is v0.1 engine (document GPU recommendation)**

4. **If all fail → Pivot or defer**
   - Option A: Position as "fast preview generation" not "audiobook production"
   - Option B: Defer v0.1 until better CPU-friendly engine emerges
   - Option C: Accept GPU requirement and document clearly

**Once engine is chosen → Kick off Phase 1 implementation**

---

## Voice Quality Gate Criteria

Before shipping v0.1, the chosen engine must pass:
- **Listening test:** 2+ testers listen to 5-minute sample
- **Question:** "Would you listen to a 10-hour audiobook in this voice?" (Yes/No)
- **Pass threshold:** ≥50% say "Yes"

**Why this matters:** Voice quality is the #1 risk. If voices sound robotic or unpleasant, users won't listen for hours, and the tool fails regardless of technical correctness.
