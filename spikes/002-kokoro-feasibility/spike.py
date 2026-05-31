"""
Spike 002: Kokoro TTS Feasibility — Quality & Performance Test

Tests Kokoro (hexgrad/Kokoro-82M) on MacBook Neo A18 Pro with MPS.
Measures RTF, generates quality samples, and assesses viability
as the v0.1 OpenNarrator engine.

Quality Gate: "Would you listen to a 10-hour audiobook in this voice?"
"""

import os
import sys
import time
import json
from pathlib import Path

import soundfile as sf
import numpy as np

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pride and Prejudice opening (same text as Piper and F5-TTS tests)
SHORT_TEXT = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife."
)

CHAPTER_TEXT = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife. "
    "However little known the feelings or views of such a man may be on his "
    "first entering a neighbourhood, this truth is so well fixed in the minds "
    "of the surrounding families, that he is considered the rightful property "
    "of some one or other of their daughters. "
    '"My dear Mr. Bennet," said his lady to him one day, "have you heard '
    'that Netherfield Park is let at last?" '
    "Mr. Bennet replied that he had not. "
    '"But it is," returned she; "for Mrs. Long has just been here, and she '
    'told me all about it." '
    "Mr. Bennet made no answer. "
    '"Do you not want to know who has taken it?" cried his wife impatiently. '
    '"You want to tell me, and I have no objection to hearing it." '
    "This was invitation enough. "
    '"Why, my dear, you must know, Mrs. Long says that Netherfield is taken '
    "by a young man of large fortune from the north of England; that he came "
    "down on Monday in a chaise and four to see the place, and was so much "
    "delighted with it, that he agreed with Mr. Morris immediately; that he "
    "is to take possession before Michaelmas, and some of his servants are to "
    'be in the house by the end of next week." '
    '"What is his name?" '
    '"Bingley." '
    '"Is he married or single?" '
    '"Oh! Single, my dear, to be sure! A single man of large fortune; four '
    'or five thousand a year. What a fine thing for our girls!" '
    '"How so? How can it affect them?" '
    '"My dear Mr. Bennet," replied his wife, "how can you be so tiresome! '
    'You must know that I am thinking of his marrying one of them." '
    '"Is that his design in settling here?" '
    '"Design! Nonsense, how can you talk so! But it is very likely that he '
    "may fall in love with one of them, and therefore you must visit him as "
    'soon as he comes." '
    '"I see no occasion for that. You and the girls may go, or you may send '
    "them by themselves, which perhaps will be still better, for as you are "
    "as handsome as any of them, Mr. Bingley may like you the best of the "
    'party."'
)


def get_duration(wav_path: str) -> float:
    """Get audio duration in seconds from a WAV file."""
    with sf.SoundFile(wav_path) as f:
        return len(f) / f.samplerate


def synthesize_to_wav(pipeline, text: str, voice: str, output_path: str) -> float:
    """Synthesize text using Kokoro pipeline and save to WAV.

    Returns synthesis time in seconds.
    """
    audio_chunks: list[np.ndarray] = []
    sample_rate = 24000  # Kokoro default sample rate

    t0 = time.perf_counter()
    for result in pipeline(text, voice=voice):
        if result is not None and hasattr(result, "audio"):
            audio_chunks.append(result.audio.cpu().numpy())
    elapsed = time.perf_counter() - t0

    if audio_chunks:
        full_audio = np.concatenate(audio_chunks)
        sf.write(output_path, full_audio, sample_rate)
    else:
        # Save empty WAV
        sf.write(output_path, np.zeros((1,)), sample_rate)

    return elapsed


def bench_voice(pipeline, device: str, voice_name: str, text: str, label: str):
    """Benchmark a single voice."""
    print(f"\n{'─' * 60}")
    print(f"[{label}] Voice: {voice_name} on {device}")
    print(f"{'─' * 60}")
    print(f"  Text: {len(text)} chars")

    # Load voice
    t0 = time.perf_counter()
    voice = pipeline.load_single_voice(voice_name)
    load_time = time.perf_counter() - t0
    print(f"  Voice load: {load_time:.3f}s")
    print(f"  Voice shape: {tuple(voice.shape)}")

    # Synthesize
    out_path = OUTPUT_DIR / f"{label}.wav"
    synth_time = synthesize_to_wav(pipeline, text, voice_name, str(out_path))
    duration = get_duration(str(out_path))
    rtf = synth_time / duration if duration > 0 else float("inf")
    size_mb = os.path.getsize(str(out_path)) / (1024 * 1024)

    print(f"  Synthesis: {synth_time:.1f}s for {duration:.1f}s audio")
    print(f"  RTF: {rtf:.2f}x")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Projection: 10h book in {rtf * 10:.1f}h")
    print(f"  File: {out_path}")

    return {
        "voice": voice_name,
        "device": device,
        "load_s": round(load_time, 3),
        "synth_s": round(synth_time, 1),
        "audio_s": round(duration, 1),
        "rtf": round(rtf, 2),
        "size_mb": round(size_mb, 2),
    }


def main():
    device = "mps"  # Use MPS on A18 Pro

    print("=" * 60)
    print("SPIKE 002: Kokoro TTS Feasibility Test")
    print(f"Device: {device}")
    print("Platform: Apple A18 Pro (MacBook Neo)")
    print("=" * 60)

    # 1. Load pipeline
    print("\n[1] Loading Kokoro pipeline (hexgrad/Kokoro-82M)...")
    sys.stdout.flush()
    t0 = time.perf_counter()
    from kokoro.pipeline import KPipeline

    pipeline = KPipeline(lang_code="a", device=device)
    load_time = time.perf_counter() - t0
    print(f"  Pipeline loaded in {load_time:.1f}s")

    # 2. Quick warmup
    print("\n[2] Warmup inference...")
    sys.stdout.flush()
    t0 = time.perf_counter()
    warmup_voice = pipeline.load_single_voice("af_bella")
    for result in pipeline(
        "The quick brown fox jumps over the lazy dog.", voice="af_bella"
    ):
        pass
    warmup_time = time.perf_counter() - t0
    print(f"  Warmup completed in {warmup_time:.1f}s")

    # 3. Benchmark voices
    results = []
    voices_to_test = [
        ("af_bella", "Short test"),
        ("af_bella", "Bella-chapter"),
    ]

    for voice_name, _ in voices_to_test[:1]:
        r = bench_voice(pipeline, device, voice_name, SHORT_TEXT, "kokoro_short")
        results.append(r)

    # 4. Full chapter sample with best voice
    print(
        f"\n[3] Generating full chapter quality sample ({len(CHAPTER_TEXT)} chars)..."
    )
    sys.stdout.flush()
    out_path = OUTPUT_DIR / "quality_sample.wav"
    synth_time = synthesize_to_wav(pipeline, CHAPTER_TEXT, "af_bella", str(out_path))
    duration = get_duration(str(out_path))
    rtf = synth_time / duration if duration > 0 else float("inf")
    size_mb = os.path.getsize(str(out_path)) / (1024 * 1024)
    print(
        f"  Synthesis: {synth_time:.1f}s for {duration:.1f}s ({duration / 60:.1f} min) audio"
    )
    print(f"  RTF: {rtf:.2f}x")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  File: {out_path}")

    results.append(
        {
            "voice": "af_bella",
            "device": device,
            "synth_s": round(synth_time, 1),
            "audio_s": round(duration, 1),
            "audio_min": round(duration / 60, 1),
            "rtf": round(rtf, 2),
            "size_mb": round(size_mb, 2),
        }
    )

    # 5. Quality gate prompt
    print("\n[4] Voice Quality Gate")
    print('  Question: "Would you listen to a 10-hour audiobook in this voice?"')
    print("  Answer: ___ (Yes/No)")

    # 6. Comparison table
    print("\n[5] Performance Comparison")
    print(f"  {'Engine':<20} {'RTF':<10} {'10h book':<15} {'Verdict':<15}")
    print(f"  {'─' * 60}")
    print(
        f"  {'Kokoro (af_bella)':<20} {rtf:<10.2f} {rtf * 10:<15.1f}h {'TESTING':<15}"
    )
    print(f"  {'Piper libritts':<20} {'0.48':<10} {'4.8':<15}h {'TESTING':<15}")
    print(f"  {'F5-TTS (MPS)':<20} {'10.48':<10} {'104.8':<15}h {'❌ TOO SLOW':<15}")

    # 7. Save results
    results_json = OUTPUT_DIR / "results.json"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(results_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {results_json}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
