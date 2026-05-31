"""
Spike 003: F5-TTS CPU/MPS Performance & Quality Test

Tests F5-TTS on MacBook Neo A18 Pro with MPS acceleration.
Measures RTF, generates quality samples, and assesses viability
as the v0.1 OpenNarrator engine.

Quality Gate: "Would you listen to a 10-hour audiobook in this voice?"
"""

import os
import sys
import time
import wave
import json
from pathlib import Path

# Use the built-in reference voice from F5-TTS examples
F5_PKG = (
    Path(__file__).parent / ".venv" / "lib" / "python3.11" / "site-packages" / "f5_tts"
)
REF_FILE = str(F5_PKG / "infer" / "examples" / "basic" / "basic_ref_en.wav")
REF_TEXT = "Some call me nature, others call me mother nature."

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pride and Prejudice opening (same text as Piper libritts test)
TEST_TEXT = (
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
    "This was invitation enough."
)

# Longer sample for quality assessment: continuation of the chapter
CHAPTER_TEXT = (
    # Narration
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


def get_audio_duration(wav_path: str) -> float:
    """Get audio duration in seconds from a WAV file."""
    with wave.open(wav_path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / rate if rate > 0 else 0.0


def main():
    results = {}
    device = "mps"  # MacBook Neo A18 Pro with MPS acceleration

    print("=" * 60)
    print("SPIKE 003: F5-TTS Performance & Quality Test")
    print(f"Device: {device}")
    print("Platform: Apple A18 Pro (MacBook Neo)")
    print("=" * 60)

    # 1. Load model
    print(f"\n[1] Loading F5TTS model on {device}...")
    sys.stdout.flush()
    t0 = time.perf_counter()
    from f5_tts.api import F5TTS

    model = F5TTS(device=device)
    load_time = time.perf_counter() - t0
    print(f"  Model loaded in {load_time:.1f}s")
    print(f"  Model type: {model.__class__.__name__}")
    results["load_time_s"] = round(load_time, 1)

    # 2. Quick warmup (short text, no WAV output)
    print("\n[2] Warmup inference...")
    sys.stdout.flush()
    t0 = time.perf_counter()
    warmup_wav = model.infer(
        ref_file=REF_FILE,
        ref_text=REF_TEXT,
        gen_text="This is a warmup test.",
        file_wave=str(OUTPUT_DIR / "warmup.wav"),
    )
    warmup_time = time.perf_counter() - t0
    print(f"  Warmup completed in {warmup_time:.1f}s")
    results["warmup_s"] = round(warmup_time, 1)

    # 3. Short sample (Pride and Prejudice opening)
    print(f"\n[3] Synthesizing short sample ({len(TEST_TEXT)} chars)...")
    sys.stdout.flush()
    t0 = time.perf_counter()
    short_wav = model.infer(
        ref_file=REF_FILE,
        ref_text=REF_TEXT,
        gen_text=TEST_TEXT,
        file_wave=str(OUTPUT_DIR / "pride_prejudice_opening.wav"),
    )
    short_time = time.perf_counter() - t0
    short_duration = get_audio_duration(str(OUTPUT_DIR / "pride_prejudice_opening.wav"))
    short_rtf = short_time / short_duration if short_duration > 0 else float("inf")
    short_size = os.path.getsize(str(OUTPUT_DIR / "pride_prejudice_opening.wav")) / 1024
    print(
        f"  {len(TEST_TEXT)} chars → {short_duration:.1f}s audio in "
        f"{short_time:.1f}s (RTF: {short_rtf:.2f}x, {short_size:.0f} KB)"
    )
    results["short_text_chars"] = len(TEST_TEXT)
    results["short_audio_s"] = round(short_duration, 1)
    results["short_synth_s"] = round(short_time, 1)
    results["short_rtf"] = round(short_rtf, 2)
    results["short_size_kb"] = round(short_size)

    # 4. Longer sample (full chapter continuation)
    full_text = TEST_TEXT + " " + CHAPTER_TEXT
    print(
        f"\n[4] Synthesizing longer sample ({len(full_text)} chars) for quality assessment..."
    )
    sys.stdout.flush()
    t0 = time.perf_counter()
    long_wav = model.infer(
        ref_file=REF_FILE,
        ref_text=REF_TEXT,
        gen_text=full_text,
        file_wave=str(OUTPUT_DIR / "quality_sample.wav"),
    )
    long_time = time.perf_counter() - t0
    long_duration = get_audio_duration(str(OUTPUT_DIR / "quality_sample.wav"))
    long_rtf = long_time / long_duration if long_duration > 0 else float("inf")
    long_size = os.path.getsize(str(OUTPUT_DIR / "quality_sample.wav")) / (1024 * 1024)
    print(
        f"  {len(full_text)} chars → {long_duration:.1f}s ({long_duration / 60:.1f} min) audio"
    )
    print(f"  Synthesis: {long_time:.1f}s (RTF: {long_rtf:.2f}x, {long_size:.1f} MB)")
    results["long_text_chars"] = len(full_text)
    results["long_audio_s"] = round(long_duration, 1)
    results["long_audio_min"] = round(long_duration / 60, 1)
    results["long_synth_s"] = round(long_time, 1)
    results["long_rtf"] = round(long_rtf, 2)
    results["long_size_mb"] = round(long_size, 1)

    # 5. Projection: 10-hour book
    print("\n[5] Performance Projection (10-hour audiobook)")
    ten_hour_seconds = 10 * 3600
    # Scale by RTF
    projected_synth = ten_hour_seconds * long_rtf
    print(f"  RTF: {long_rtf:.2f}x")
    print(f"  10-hour book projection: {projected_synth / 3600:.1f} hours of synthesis")
    print(f"  Real-time capable: {'YES ✅' if long_rtf < 1.0 else 'NO ❌'}")
    print(f"  Faster-than-real-time: {'YES ✅' if long_rtf < 0.5 else 'NO'}")
    results["ten_hour_projection_h"] = round(projected_synth / 3600, 1)
    results["real_time_capable"] = long_rtf < 1.0
    results["faster_than_real_time"] = long_rtf < 0.5

    # 6. Quality assessment prompt
    print("\n[6] Voice Quality Gate")
    print(f"  Listen to: {OUTPUT_DIR / 'quality_sample.wav'}")
    print('  Question: "Would you listen to a 10-hour audiobook in this voice?"')
    print("  Answer: ___ (Yes/No)")
    print("")
    print("  Compare with Piper libritts (if available):")
    print("    Piper libritts RTF: 0.48x (was ~5h for a 10h book)")
    print(f"    F5-TTS RTF:         {long_rtf:.2f}x")

    # 7. Save results
    results_json = OUTPUT_DIR / "results.json"
    with open(results_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {results_json}")

    print(f"\n{'=' * 60}")
    print("TEST COMPLETE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
