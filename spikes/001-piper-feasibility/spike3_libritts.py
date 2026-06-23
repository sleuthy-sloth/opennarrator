"""Spike 003: Piper libritts voice quality test.

Tests the en_US-libritts voice (trained on LibriTTS audiobook data)
against the voice quality gate criteria.

Quality Gate: "Would you listen to a 10-hour audiobook in this voice?"
"""

import time
import wave
from pathlib import Path

from piper.voice import PiperVoice

MODEL_PATH = Path("voices/en_US-libritts/en/en_US/libritts/high/en_US-libritts-high.onnx")
OUTPUT_DIR = Path("spikes/001-piper-feasibility/output-libritts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TEST_TEXT = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife. "
    "However little known the feelings or views of such a man may be on his "
    "first entering a neighbourhood, this truth is so well fixed in the minds "
    "of the surrounding families, that he is considered the rightful property "
    "of some one or other of their daughters. "
    "\"My dear Mr. Bennet,\" said his lady to him one day, \"have you heard "
    "that Netherfield Park is let at last?\" "
    "Mr. Bennet replied that he had not. "
    "\"But it is,\" returned she; \"for Mrs. Long has just been here, and she "
    "told me all about it.\" "
    "Mr. Bennet made no answer. "
    "\"Do you not want to know who has taken it?\" cried his wife impatiently. "
    "\"You want to tell me, and I have no objection to hearing it.\" "
    "This was invitation enough. "
    "\"Why, my dear, you must know, Mrs. Long says that Netherfield is taken "
    "by a young man of large fortune from the north of England; that he came "
    "down on Monday in a chaise and four to see the place, and was so much "
    "delighted with it, that he agreed with Mr. Morris immediately; that he "
    "is to take possession before Michaelmas, and some of his servants are to "
    "be in the house by the end of next week.\" "
    "\"What is his name?\" "
    "\"Bingley.\" "
    "\"Is he married or single?\" "
    "\"Oh! Single, my dear, to be sure! A single man of large fortune; four "
    "or five thousand a year. What a fine thing for our girls!\" "
    "\"How so? How can it affect them?\" "
    "\"My dear Mr. Bennet,\" replied his wife, \"how can you be so tiresome! "
    "You must know that I am thinking of his marrying one of them.\" "
    "\"Is that his design in settling here?\" "
    "\"Design! Nonsense, how can you talk so! But it is very likely that he "
    "may fall in love with one of them, and therefore you must visit him as "
    "soon as he comes.\" "
    "\"I see no occasion for that. You and the girls may go, or you may send "
    "them by themselves, which perhaps will be still better, for as you are "
    "as handsome as any of them, Mr. Bingley may like you the best of the "
    "party.\""
)

SHORT_TEXT = (
    "The sun rose slowly over the distant mountains, casting long shadows "
    "across the valley below. Birds began their morning chorus as the world "
    "stirred from its slumber."
)


def synthesize(voice: PiperVoice, text: str, label: str) -> float:
    """Synthesize text, save WAV, return elapsed seconds."""
    output_path = OUTPUT_DIR / f"{label}.wav"
    start = time.perf_counter()
    with wave.open(str(output_path), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    elapsed = time.perf_counter() - start

    with wave.open(str(output_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / rate

    rtf = elapsed / duration if duration > 0 else float("inf")
    size_kb = output_path.stat().st_size / 1024
    print(f"  [{label}] {len(text)} chars → {duration:.1f}s audio in {elapsed:.1f}s "
          f"(RTF: {rtf:.2f}x, {size_kb:.0f} KB)")
    return duration


def main():
    print("=" * 60)
    print("SPIKE 003: Piper libritts Voice Quality Test")
    print("=" * 60)

    # 1. Load voice
    print("\n[1] Loading libritts voice (high quality)...")
    t0 = time.perf_counter()
    voice = PiperVoice.load(str(MODEL_PATH))
    model_path = "en_US-libritts-high.onnx"
    model_mb = MODEL_PATH.stat().st_size / (1024 * 1024)
    load_time = time.perf_counter() - t0
    print(f"  Loaded in {load_time:.1f}s ({model_mb:.0f} MB model)")

    # 2. Short test (warmup)
    print("\n[2] Short warmup test:")
    synthesize(voice, SHORT_TEXT, "warmup")

    # 3. Pride and Prejudice opening (quality test)
    print("\n[3] Pride and Prejudice opening (dialogue + narration):")
    total_duration = synthesize(voice, TEST_TEXT, "pride_prejudice_opening")

    # 4. Repeat to fill 5 minutes (quality gate requires 5-min sample)
    print("\n[4] Generating longer sample (~5 min target)...")
    # Repeat the text multiple times to approach 5 minutes
    total_chars = len(TEST_TEXT)
    total_synth_time = 0.0
    total_duration = 0.0
    iteration = 0
    target_duration = 300  # 5 minutes

    # First estimate: how many iterations needed?
    # From first synthesis, calculate chars per second of audio
    first_duration = total_duration
    if first_duration > 0:
        chars_per_sec = total_chars / first_duration
        iterations_needed = int(target_duration * chars_per_sec / total_chars) + 1
        print(f"  Estimated iterations needed: ~{iterations_needed}")
    else:
        iterations_needed = 10

    # Synthesize all iterations into one WAV
    output_path = OUTPUT_DIR / "libritts_5min_sample.wav"
    start = time.perf_counter()

    # Use a single WAV file approach: synthesize iteratively to get timing
    for i in range(iterations_needed):
        text = TEST_TEXT
        if i > 0:
            text = " " + text  # spacing between iterations
        # Just measure, don't save individual files
        pass

    # Actually, let's synthesize the full sample properly
    # Build one big text blob
    big_text = " . ".join([str(i + 1) + ". " + TEST_TEXT for i in range(iterations_needed)])

    print(f"  Synthesizing {len(big_text)} characters ({len(big_text)//1000}K chars)...")
    t0 = time.perf_counter()
    with wave.open(str(output_path), "wb") as wav_file:
        voice.synthesize_wav(big_text, wav_file)
    synth_time = time.perf_counter() - t0

    with wave.open(str(output_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / rate

    rtf = synth_time / duration if duration > 0 else float("inf")
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Total: {duration/60:.1f} min audio in {synth_time:.1f}s (RTF: {rtf:.2f}x, {size_mb:.1f} MB)")

    # 5. Performance summary
    print("\n[5] Performance Summary:")
    print(f"  Model: libritts-high ({model_mb:.0f} MB)")
    print(f"  Load time: {load_time:.1f}s")
    print(f"  RTF (overall): {rtf:.2f}x")
    print(f"  Projection: 10-hour book in {rtf * 10:.1f} hours")
    print(f"  Sample file: {output_path}")

    # 6. Quality assessment (subjective — manual)
    print("\n[6] Voice Quality Assessment:")
    print(f"  Listen to: {output_path}")
    print("  Question: \"Would you listen to a 10-hour audiobook in this voice?\"")
    print("  Answer: ___ (Yes/No)")
    print("  Notes: ________________________________________")


if __name__ == "__main__":
    main()
