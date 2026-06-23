"""
Quick RTF benchmark: F5-TTS on MPS vs CPU on A18 Pro.

Short and focused — just measures synthesis speed.
"""

import time
import wave
from pathlib import Path

F5_PKG = (
    Path(__file__).parent / ".venv" / "lib" / "python3.11" / "site-packages" / "f5_tts"
)
REF_FILE = str(F5_PKG / "infer" / "examples" / "basic" / "basic_ref_en.wav")
REF_TEXT = "Some call me nature, others call me mother nature."

SHORT_TEXT = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife."
)

MEDIUM_TEXT = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife. "
    "However little known the feelings or views of such a man may be on his "
    "first entering a neighbourhood, this truth is so well fixed in the minds "
    "of the surrounding families, that he is considered the rightful property "
    "of some one or other of their daughters."
)


def get_duration(wav_path):
    with wave.open(wav_path, "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def bench(device, label, text, output_name):
    print(f"\n{'=' * 60}")
    print(f"[{label}] Testing F5-TTS on device={device}")
    print(f"  Text: {len(text)} chars")
    print(f"{'=' * 60}")

    # Import here so device switching is clean
    import gc

    from f5_tts.api import F5TTS

    t0 = time.perf_counter()
    model = F5TTS(device=device)
    load_time = time.perf_counter() - t0
    print(f"  Load: {load_time:.1f}s")

    out_path = Path(__file__).parent / "output" / f"{output_name}.wav"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    model.infer(
        ref_file=REF_FILE,
        ref_text=REF_TEXT,
        gen_text=text,
        file_wave=str(out_path),
    )
    elapsed = time.perf_counter() - t0
    duration = get_duration(str(out_path))
    rtf = elapsed / duration if duration > 0 else float("inf")

    print(f"  Synthesis: {elapsed:.1f}s for {duration:.1f}s audio")
    print(f"  RTF: {rtf:.2f}x")
    print(f"  Projection: 10h book in {rtf * 10:.1f}h")

    # Clean up for next test
    del model
    gc.collect()
    if device == "mps":
        import torch

        torch.mps.empty_cache()

    return {
        "device": device,
        "load_s": load_time,
        "synth_s": elapsed,
        "audio_s": duration,
        "rtf": rtf,
    }


def main():
    results = []

    # Test 1: MPS, short text (1 sentence)
    r = bench("mps", "MPS short", SHORT_TEXT, "mps_short")
    results.append(r)

    # Test 2: CPU, short text (1 sentence) if MPS is too slow
    if r["rtf"] > 2:
        r2 = bench("cpu", "CPU short", SHORT_TEXT, "cpu_short")
        results.append(r2)

    # Print summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    for r in results:
        print(
            f"  {r['device']}: RTF {r['rtf']:.2f}x, 10h book → {r['rtf'] * 10:.1f}h "
            f"(load {r['load_s']:.1f}s, synth {r['synth_s']:.1f}s for {r['audio_s']:.1f}s audio)"
        )


if __name__ == "__main__":
    main()
