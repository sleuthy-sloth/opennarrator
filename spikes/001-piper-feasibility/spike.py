"""Spike 001: Piper TTS feasibility test.

Validates:
1. Voice loading from ONNX model
2. Text-to-speech synthesis
3. Speed measurement (real-time factor)
4. WAV file output quality
"""

import time
from pathlib import Path

from piper.voice import PiperVoice


MODEL_PATH = Path("voices/en_US-lessac/en/en_US/lessac/medium/en_US-lessac-medium.onnx")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def test_single_sentence(voice: PiperVoice, text: str, label: str) -> float:
    """Synthesize one sentence, save WAV, return seconds of audio."""
    output_path = OUTPUT_DIR / f"{label}.wav"
    start = time.perf_counter()
    
    import wave
    with wave.open(str(output_path), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    
    elapsed = time.perf_counter() - start
    
    # Get audio duration from WAV file
    import wave
    with wave.open(str(output_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / rate
    
    rtf = elapsed / duration if duration > 0 else float("inf")
    print(f"  [{label}] Text: {len(text)} chars → {duration:.2f}s audio in {elapsed:.2f}s (RTF: {rtf:.1f}x)")
    return duration


def main():
    print("=" * 60)
    print("SPIKE 001: Piper TTS Feasibility")
    print("=" * 60)
    
    # 1. Load voice
    print("\n[1] Loading voice model...")
    t0 = time.perf_counter()
    voice = PiperVoice.load(str(MODEL_PATH))
    load_time = time.perf_counter() - t0
    print(f"  Loaded in {load_time:.2f}s")
    
    # 2. Single sentence
    print("\n[2] Single sentence test:")
    test_single_sentence(
        voice,
        "The quick brown fox jumped over the lazy dog.",
        "sentence",
    )
    
    # 3. Paragraph
    print("\n[3] Paragraph test:")
    paragraph = (
        "It was the best of times, it was the worst of times. "
        "The sun rose slowly over the distant mountains, casting long shadows "
        "across the valley below. Birds began their morning chorus as the world "
        "stirred from its slumber. A gentle breeze carried the scent of pine "
        "through the crisp morning air."
    )
    test_single_sentence(voice, paragraph, "paragraph")
    
    # 4. Speed benchmark: multiple sentences
    print("\n[4] Speed benchmark (5 sentences):")
    sentences = [
        "The laboratory was quiet except for the hum of machinery.",
        "She had never seen anything quite like it before in her entire life.",
        "Data streams flowed across the displays in real time.",
        "The algorithm had been running for forty eight hours straight.",
        "Tomorrow would bring new challenges and unexpected discoveries.",
    ]
    
    total_chars = sum(len(s) for s in sentences)
    t0 = time.perf_counter()
    for i, sentence in enumerate(sentences):
        test_single_sentence(voice, sentence, f"bench_{i+1}")
    total_elapsed = time.perf_counter() - t0
    print(f"  Total: {total_chars} chars in {total_elapsed:.2f}s")
    
    # 5. List output files
    print("\n[5] Output files:")
    for wav in sorted(OUTPUT_DIR.glob("*.wav")):
        size_kb = wav.stat().st_size / 1024
        print(f"  {wav.name}: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
