# Spike 001: Piper TTS Feasibility

**Date:** 2026-05-27
**Status:** Complete

## Question

Can Piper TTS serve as the first TTS engine for OpenNarrator? Specifically:
1. Can we load a voice model and synthesize text via Python API?
2. Is the synthesis speed acceptable for full audiobook production?
3. Is the voice quality good enough for long-form narration?
4. Can we download voice models programmatically via HuggingFace?

---

## Verdict: PARTIAL ✅⚠️

Piper is **technically excellent** but **voice quality is unvalidated** for long-form narration.

**Validated ✅**
- Speed: RTF 0.1-0.2x on Pi 5 (fast enough for real-time audiobook production)
- API: Clean Python interface, subprocess-isolation friendly
- Voice downloads: Works via HuggingFace, no auth required

**Unvalidated / Failed ⚠️**
- Voice quality: `en_US-lessac` sounds robotic even with tuning — **failed subjective quality gate** ("Would you listen to a 10-hour book in this voice?" → No)
- `en_US-libritts` (audiobook-trained voice) remains untested — this is the next critical test

**Recommendation:** Piper is the right *engine* choice for v0.1 (fast, CPU-friendly, clean API), but we cannot commit to it for v0.1 until either `libritts` passes the quality gate or Kokoro is evaluated as an alternative. See [Voice Quality Requirements](../../docs/SPEC.md#voice-quality-requirements) in the spec.

---

## What worked

### Voice model download
- `hf download rhasspy/piper-voices --include "en/en_US/lessac/*.onnx"` works cleanly
- Voices come in low/medium/high quality tiers (ONNX files + JSON configs)
- No authentication required (higher rate limits with token)
- Files total ~50MB per voice — very manageable

### Synthesis speed (critical for audiobooks)
- **RTF: 0.1-0.2x** on Raspberry Pi 5 (ARM Cortex-A76, 4 cores)
- 291-character paragraph → 15s audio in 1.87s
- On M-series Mac: expected RTF < 0.05x (faster than real-time by 20x+)
- **Projection:** A 10-hour audiobook (~900K chars) would process in ~1 hour on Pi, ~15 minutes on Mac

### Python API
- `PiperVoice.load(model_path)` — class method, 2.4s load time on Pi
- `synthesize_wav(text, wav_file)` — writes directly to WAV, simple
- `synthesize(text)` — returns iterator of AudioChunk (per-sentence chunks, alignment data)
- `phonemize(text)` / `phonemes_to_ids()` — exposed for custom pipelines
- `list_voices()` — not built-in, but model discovery via HuggingFace API is straightforward

### espeak-ng phonemization
- Bundled with the pip package (no separate install)
- Works out of the box for English
- Handles punctuation, numbers, and basic SSML-like features via text

---

## What didn't

### API quirk: `synthesize_wav` requires `wave.Wave_write`
```python
# WRONG — raises AttributeError
with open("out.wav", "wb") as f:
    voice.synthesize_wav(text, f)

# CORRECT
import wave
with wave.open("out.wav", "wb") as wav_file:
    voice.synthesize_wav(text, wav_file)
```
The engine adapter must import `wave` and create proper `Wave_write` objects. Document this.

### Voice discovery is manual
Piper doesn't have a built-in "list available voices" function. We'll need to:
1. Parse the HuggingFace repo structure (`rhasspy/piper-voices`)
2. Or maintain a voice registry JSON
3. Or let users specify model paths directly

### espeak-ng data directory warning
Piper prints ONNX warnings about GPU detection on every load (harmless but noisy). The espeak data directory defaults to the pip package path — if we use subprocess isolation with a different venv, espeak data might not be found. We'll need to pass `espeak_data_dir` explicitly.

---

## Surprises

1. **Piper is much faster than expected on ARM.** RTF 0.1x on a Pi 5 means real-time audiobook production is viable even on low-end hardware. This was the biggest risk and it cleared easily.

2. **The Python API is richer than documented.** `phonemize()`, `phonemes_to_ids()`, and `phoneme_ids_to_audio()` are all exposed — we can build custom text preprocessing (pronunciation overrides, SSML-to-phoneme mapping) without modifying Piper.

3. **No GPU needed for good quality.** The medium-quality ONNX model produces clear, intelligible speech on CPU. The high-quality model is only marginally larger — worth testing on Mac for even better output.

4. **HuggingFace download is slow on first run.** ~35 seconds for a 50MB voice. Caching will be essential for UX. Consider bundling a default voice or providing a `--voice-url` option.

---

## Recommendation for the real build

1. **Use `PiperVoice.load()` + `synthesize_wav()`** as the primary interface. Clean, simple, proven.
2. **Subprocess isolation per chapter** — load voice once, synthesize all sentences in that chapter, write one WAV. Next chapter: new subprocess loads voice fresh (GPU memory safety).
3. **Voice manager should cache models** in `~/.cache/opennarrator/voices/` using the HuggingFace structure.
4. **Support all three quality tiers** — `--quality low|medium|high` CLI flag. Low for previews, high for final output.
5. **Bundle espeak data path** — pass `espeak_data_dir` from the engine adapter to handle subprocess venv differences.
6. **Test the `lessac` voice on Mac** — quality assessment needed from the target platform.
7. **Consider `synthesize()` for streaming** — if we want per-sentence progress bars, use `synthesize()` to get `AudioChunk` iterators and report progress sentence-by-sentence.

---

## Update: `en_US-libritts` Voice Test (2026-05-27)

### Results

| Metric | Value |
|--------|-------|
| **Model** | `en_US-libritts-high` (137 MB ONNX) |
| **Test text** | Pride & Prejudice Ch.1 opening (2,428 chars) |
| **Audio output** | 2.1 minutes (125.6 seconds) |
| **Synthesis time** | 60.3 seconds |
| **RTF** | 0.48x (2x faster than real-time) |
| **Model load** | 0.3-0.4 seconds |
| **Projection** | 10-hour book in ~4.8 hours |
| **Platform** | Apple Silicon arm64 (CPU-only) |

### Quality Assessment

**Status:** AWAITING ASSESSMENT

The 2.1-minute sample was synthesized successfully. The `libritts` voice (trained on LibriTTS audiobook recordings) sounds noticeably different from `lessac` — less robotic, more natural pacing. However, the final quality gate decision requires listener feedback.

**Sample file:** `spikes/001-piper-feasibility/output-libritts/libritts_quality_test.wav`

**Quality Gate Question:** "Would you listen to a 10-hour audiobook narrated in this voice?"

### Next Steps

- If `libritts` passes quality gate → **Piper confirmed as v0.1 engine**
- If `libritts` fails → proceed to Kokoro testing (Spike 002)
- If Kokoro also fails → validate F5-TTS CPU performance (Spike 003)

### Spike Files

| File | Description |
|------|-------------|
| `spike3_libritts.py` | libritts voice synthesis test script |
| `output-libritts/libritts_quality_test.wav` | 2.1-min quality test sample |
| `output-libritts/quicktest.wav` | Quick 3-second warmup test |
| `output-libritts/libritts_sample.wav` | 42-second medium sample |
