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

## Verdict: VALIDATED ✅

Piper is an excellent first engine for OpenNarrator. It's fast, CPU-friendly, and has a clean Python API suitable for subprocess isolation.

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
