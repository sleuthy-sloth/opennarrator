# TTS Engine Comparison

Last updated: 2026-05-27

## Comparison Matrix

| Engine | License | Quality | Speed (CPU) | GPU Required | Voice Cloning | Languages | Model Size |
|--------|---------|---------|-------------|-------------|---------------|-----------|------------|
| **Piper** | MIT | ★★★☆☆ ⚠️ | **Very Fast** (RTF 0.1-0.2x on Pi 5) | No | No (50+ pre-trained voices) | 30+ languages | ~50MB per voice |
| **Kokoro** | Apache 2.0 | ★★★★☆ (reported) | Fast (CPU) | No | No (pre-trained voices) | English, Japanese, Chinese, Korean, French | ~80MB |
| **F5-TTS** | MIT | ★★★★★ | **Unknown** (CPU untested) | **Maybe** (CUDA/MPS) | Yes (best open-source cloning) | English (primary), multi-lingual emerging | ~300MB |
| **XTTSv2** | Non-commercial | ★★★★☆ | Fast (GPU) | Yes | Yes (good cloning) | 16 languages | ~1.8GB |
| **Bark** | MIT | ★★★☆☆ | Slow (GPU) | Yes (heavy) | Yes (speaker prompts) | English, multi-lingual | ~4GB |
| **Coqui TTS** | Apache 2.0 | ★★★☆☆ | Medium | Optional | Yes (XTTS fork) | Multi-lingual | Varies |

**Key:** ⚠️ = Voice quality gate failed (see Spike Results below)

## OpenNarrator Support Roadmap

| Engine | v0.1 Status | v0.2 | v0.3 |
|--------|-------------|------|------|
| **Piper** | 🔄 Testing (`libritts` voice) | ✅ | ✅ |
| **Kokoro** | 🔄 Testing (blocked on Pi, pending MacBook Neo) | ✅ | ✅ |
| **F5-TTS** | ⚠️ Fallback (CPU perf unvalidated on A18 Pro) | ✅ Voice cloning | ✅ Primary engine |
| XTTSv2 | — | — | ❌ License incompatible |
| Bark | — | — | ❌ Too slow, too large |

**Current Status:** Engine selection in progress. See Phase 0 in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

---

## Spike Results (Real-World Testing)

### Spike 001: Piper TTS — PARTIAL ✅⚠️

**Tested:** 2026-05-27 on Raspberry Pi 5 (ARM Cortex-A76, 4 cores)

**Benchmark Results:**
- **RTF: 0.1-0.2x** (10-20x faster than real-time)
- **Projection:** 10-hour audiobook processes in ~1 hour on Pi 5, ~15 minutes on MacBook Neo
- **Model load time:** 2.4 seconds on Pi 5
- **Voice tested:** `en_US-lessac-medium` (50MB ONNX model)

**What Worked ✅:**
- Speed is excellent for CPU-only audiobook production
- Clean Python API: `PiperVoice.load(model_path)` + `synthesize_wav(text, wave_file)`
- Voice downloads work via HuggingFace CLI (no auth required)
- Subprocess isolation straightforward
- espeak-ng phonemization bundled with pip package

**What Failed ❌:**
- **Voice quality:** `en_US-lessac` sounds robotic even with `length_scale`/`noise_scale` tuning
- **Failed quality gate:** Testers would not listen to a 10-hour book in this voice
- **Voice discovery:** No built-in "list available voices" function (manual registry needed)

**API Quirks:**
```python
# WRONG — raises AttributeError
with open("out.wav", "wb") as f:
    voice.synthesize_wav(text, f)

# CORRECT — requires wave.Wave_write object
import wave
with wave.open("out.wav", "wb") as wav_file:
    voice.synthesize_wav(text, wav_file)
```

**Untested:**
- `en_US-libritts` voice (trained on LibriTTS audiobook data — may sound more natural)
- High-quality model tier (only tested medium)

**Verdict:** Piper is technically excellent (fast, clean API, CPU-friendly) but voice quality is unvalidated for long-form narration. Testing `libritts` next.

---

### Spike 002: Kokoro — BLOCKED (Pi), PENDING (MacBook Neo)

**Status:** Not yet tested. Blocked on Raspberry Pi 5 due to Python 3.13 incompatibility (`misaki` dependency requires Python < 3.13).

**Plan:** Test on MacBook Neo (likely has Python 3.12) as next priority.

**Why Kokoro Matters:**
- Apache 2.0 license (more permissive than some alternatives)
- Reportedly more natural-sounding than Piper
- Small model size (~80MB)
- CPU-friendly (no GPU required)
- Multi-language support (English, Japanese, Chinese, Korean, French)

**Risk:** If Kokoro also fails quality gate, we may need to accept F5-TTS GPU requirement or pivot value proposition.

---

### Spike 003: F5-TTS CPU Performance — NOT STARTED

**Status:** Not yet tested. Critical to validate on MacBook Neo (A18 Pro, no MPS GPU).

**Why This Matters:**
- F5-TTS has the best voice quality (state-of-the-art open-source)
- Supports voice cloning (30-second sample → custom voice)
- MIT license (fully open)
- **But:** May require GPU for acceptable performance

**Test Plan:**
1. Install F5-TTS on MacBook Neo
2. Synthesize 1-minute sample, measure RTF
3. **Acceptable:** RTF < 0.5x (2x slower than real-time)
4. **Marginal:** RTF 0.5-1.0x (usable but slow)
5. **Unacceptable:** RTF > 1.0x (slower than real-time)

**Impact:** If F5-TTS is too slow on CPU, we either:
- Accept GPU requirement (document clearly, users need NVIDIA GPU)
- Pivot value proposition (fast preview generation, not audiobook production)
- Defer v0.1 until better CPU-friendly engine emerges

---

## Voice Quality Gate

Before shipping v0.1, the chosen engine must pass a **voice quality gate**:

**Test Methodology:**
1. Synthesize 5-minute sample from a real book chapter (e.g., Project Gutenberg)
2. 2+ testers listen to the sample
3. Answer: "Would you listen to a 10-hour audiobook narrated in this voice?" (Yes/No)
4. **Pass threshold:** ≥50% of testers say "Yes"

**Current Status:**
| Voice | Engine | Quality Gate | Notes |
|-------|--------|--------------|-------|
| `en_US-lessac` | Piper | ❌ Failed | Sounds robotic, testers would not listen for hours |
| `en_US-libritts` | Piper | 🔄 Untested | Trained on audiobook data, may sound more natural |
| Kokoro default | Kokoro | 🔄 Untested | Reportedly more natural, testing on MacBook Neo next |

**Why This Matters:**
Voice quality is the #1 risk for OpenNarrator. Users will listen for hours — if the voice is robotic, unpleasant, or fatiguing, the tool fails regardless of technical correctness. We'd rather delay v0.1 than ship with bad voice quality.

---

## Why Piper First? (With Caveats)

**Original Rationale:**
1. **CPU-only** — runs on any machine, no CUDA/MPS setup required
2. **MIT license** — no restrictions
3. **50+ voices** — plenty for testing the pipeline
4. **Subprocess-friendly** — simple CLI interface, easy to isolate
5. **Fast iteration** — 10-20x real-time on modern CPU, great for development

**Updated Rationale (Post-Spike):**
Piper is still the right *engine* choice for v0.1 (fast, clean API, CPU-friendly), but we cannot commit to it until a voice passes the quality gate. The `lessac` voice failed, but `libritts` (audiobook-trained) may succeed.

**Fallback Strategy:**
If Piper `libritts` fails quality gate → test Kokoro → if Kokoro fails → validate F5-TTS CPU performance → if F5-TTS too slow on CPU → pivot or defer.

The pipeline architecture doesn't care which engine is behind `BaseTTSEngine`. Swapping engines is a one-file change. The critical path is finding a voice that sounds good enough for long-form listening.
