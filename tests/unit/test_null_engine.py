"""Tests for NullEngine."""

import struct
import wave
from pathlib import Path

from opennarrator.engines.null_engine import NullEngine


def test_null_engine_synthesize_creates_wav(tmp_path: Path) -> None:
    """synthesize() should produce a valid WAV file."""
    engine = NullEngine()
    output = tmp_path / "test.wav"
    result = engine.synthesize("hello world", "silence", output)

    assert result == output
    assert output.exists()
    assert output.stat().st_size > 0


def test_null_engine_synthesize_duration(tmp_path: Path) -> None:
    """The WAV should be approximately 1 second of audio."""
    engine = NullEngine()
    output = tmp_path / "duration.wav"
    engine.synthesize("text", "silence", output)

    with wave.open(str(output), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / rate

    # Allow slight variation due to sample count rounding
    assert 0.95 <= duration <= 1.05


def test_null_engine_synthesize_silence(tmp_path: Path) -> None:
    """All audio samples should be zero (silence)."""
    engine = NullEngine()
    output = tmp_path / "silence.wav"
    engine.synthesize("text", "silence", output)

    with wave.open(str(output), "rb") as wf:
        frames = wf.getnframes()
        # Read first 1000 frames and verify they're zero
        raw = wf.readframes(min(frames, 1000))

    for sample_start in range(0, len(raw), 2):
        (value,) = struct.unpack_from("<h", raw, sample_start)
        assert value == 0, f"Sample at offset {sample_start} is {value}, expected 0"


def test_null_engine_list_voices() -> None:
    """list_voices() should return at least one voice."""
    engine = NullEngine()
    voices = engine.list_voices()
    assert len(voices) >= 1
    assert voices[0].name == "silence"
    assert voices[0].engine == "null"
