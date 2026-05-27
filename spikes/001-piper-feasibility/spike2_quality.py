"""Spike 002: Voice quality tuning — less rushed, less robotic."""

import time
import wave
from pathlib import Path

from piper.voice import PiperVoice
from piper.config import SynthesisConfig

VOICES_DIR = Path("voices/en_US-lessac/en/en_US/lessac")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

TEST_TEXT = (
    "It was the best of times, it was the worst of times. "
    "The sun rose slowly over the distant mountains, casting long shadows "
    "across the valley below. Birds began their morning chorus as the world "
    "stirred from its slumber."
)


def synthesize(voice: PiperVoice, text: str, label: str, syn_config=None):
    output_path = OUTPUT_DIR / f"{label}.wav"
    start = time.perf_counter()
    with wave.open(str(output_path), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file, syn_config=syn_config)
    elapsed = time.perf_counter() - start
    with wave.open(str(output_path), "rb") as wf:
        duration = wf.getnframes() / wf.getframerate()
    print(f"  {label}: {duration:.1f}s audio in {elapsed:.2f}s | {output_path.name}")
    return output_path


def main():
    print("=" * 60)
    print("SPIKE 002: Voice Quality Tuning")
    print("=" * 60)

    # A) Medium quality baseline (what we already tested)
    print("\n[A] Medium quality — baseline (for comparison):")
    voice_med = PiperVoice.load(str(VOICES_DIR / "medium/en_US-lessac-medium.onnx"))
    synthesize(voice_med, TEST_TEXT, "a_medium_baseline")

    # B) High quality, default speed
    print("\n[B] High quality — default speed:")
    voice_high = PiperVoice.load(str(VOICES_DIR / "high/en_US-lessac-high.onnx"))
    synthesize(voice_high, TEST_TEXT, "b_high_default")

    # C) High quality, slower pace
    print("\n[C] High quality — length_scale=1.15 (slightly slower):")
    syn_c = SynthesisConfig(length_scale=1.15)
    synthesize(voice_high, TEST_TEXT, "c_high_slower_115", syn_config=syn_c)

    # D) High quality, even slower
    print("\n[D] High quality — length_scale=1.3 (noticeably slower):")
    syn_d = SynthesisConfig(length_scale=1.3)
    synthesize(voice_high, TEST_TEXT, "d_high_slower_130", syn_config=syn_d)

    # E) High quality, slower + noise variation
    print("\n[E] High quality — length_scale=1.15 + noise_scale=0.5 (less robotic):")
    syn_e = SynthesisConfig(length_scale=1.15, noise_scale=0.5)
    synthesize(voice_high, TEST_TEXT, "e_high_slower_noisy", syn_config=syn_e)

    print("\n✅ Done. Listen and compare.")
    print(f"Files in: {OUTPUT_DIR.resolve()}/")
    for wav in sorted(OUTPUT_DIR.glob("*.wav")):
        if wav.name.startswith(("a_", "b_", "c_", "d_", "e_")):
            print(f"  {wav.name}")


if __name__ == "__main__":
    main()
