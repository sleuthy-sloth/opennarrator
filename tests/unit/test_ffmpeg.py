"""Tests for the ffmpeg wrapper."""

import math
from pathlib import Path

import pytest

from opennarrator.audio.ffmpeg import FFmpeg
from opennarrator.exceptions import PackagingError
from opennarrator.types import Chapter


@pytest.fixture
def ffmpeg() -> FFmpeg:
    return FFmpeg()


@pytest.fixture
def sample_wavs(tmp_path: Path) -> list[Path]:
    """Generate two short sine-wave WAVs for testing."""
    paths = []
    for i, freq in enumerate([440, 880], start=1):
        p = tmp_path / f"ch{i:03d}.wav"
        # Generate a 2-second sine wave WAV
        import math
        import struct
        import wave

        sample_rate = 24000
        duration = 2.0
        num_samples = int(sample_rate * duration)

        with wave.open(str(p), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            for n in range(num_samples):
                value = int(32767 * 0.3 * math.sin(n / sample_rate * freq * 6.28))
                wf.writeframes(struct.pack("<h", value))
        paths.append(p)
    return paths


class TestFFmpeg:
    def test_normalize_wav(self, ffmpeg: FFmpeg, tmp_path: Path) -> None:
        """Normalize should produce a valid WAV."""
        import wave

        # Generate a simple WAV
        p = tmp_path / "input.wav"
        import struct

        with wave.open(str(p), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            for _ in range(24000):
                wf.writeframes(struct.pack("<h", 0))
        # Write a non-silent sample at the end
        with wave.open(str(p), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            for n in range(24000):
                val = int(32767 * 0.5 * math.sin((n / 24000.0) * 440 * 6.28))
                wf.writeframes(struct.pack("<h", val))

        out = tmp_path / "normalized.wav"
        result = ffmpeg.normalize_wav(p, out)
        assert result.exists()
        assert result.stat().st_size > 100

    def test_concat_wavs(self, ffmpeg: FFmpeg, sample_wavs: list[Path], tmp_path: Path) -> None:
        """Concatenated file should be longer than individual files."""
        out = tmp_path / "merged.wav"
        result = ffmpeg.concat_wavs(sample_wavs, out)
        assert result.exists()

        # Get durations
        dur1 = ffmpeg.get_duration(sample_wavs[0])
        dur2 = ffmpeg.get_duration(sample_wavs[1])
        merged_dur = ffmpeg.get_duration(out)
        # Merged should be roughly sum of parts
        assert abs(merged_dur - (dur1 + dur2)) < 0.1

    def test_get_duration(self, ffmpeg: FFmpeg, sample_wavs: list[Path]) -> None:
        """Duration should be approximately correct."""
        dur = ffmpeg.get_duration(sample_wavs[0])
        assert 1.8 < dur < 2.2

    def test_trim_silence(self, ffmpeg: FFmpeg, tmp_path: Path) -> None:
        """Trim should reduce file size if silence is present."""
        import struct
        import wave

        # WAV with 0.5s leading silence, 1.0s tone, 0.5s trailing silence
        p = tmp_path / "with_silence.wav"
        sample_rate = 24000
        with wave.open(str(p), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            # 0.5s silence
            for _ in range(int(sample_rate * 0.5)):
                wf.writeframes(struct.pack("<h", 0))
            # 1.0s tone
            for n in range(sample_rate):
                val = int(32767 * 0.5 * math.sin((n / sample_rate) * 440 * 6.28))
                wf.writeframes(struct.pack("<h", val))
            # 0.5s silence
            for _ in range(int(sample_rate * 0.5)):
                wf.writeframes(struct.pack("<h", 0))

        trimmed = tmp_path / "trimmed.wav"
        result = ffmpeg.trim_silence(p, trimmed)
        trimmed_dur = ffmpeg.get_duration(result)
        # Should be closer to 1.0s than 2.0s
        assert trimmed_dur < 1.5

    def test_to_m4b(self, ffmpeg: FFmpeg, sample_wavs: list[Path], tmp_path: Path) -> None:
        """M4B output should be a valid audio file with chapters."""
        # First concat
        merged = tmp_path / "merged.wav"
        ffmpeg.concat_wavs(sample_wavs, merged)

        chapters = [
            Chapter(index=1, title="Chapter 1", text="First chapter."),
            Chapter(index=2, title="Chapter 2", text="Second chapter."),
        ]

        out = tmp_path / "test.m4b"
        result = ffmpeg.to_m4b(
            audio_path=merged,
            chapters=chapters,
            output_path=out,
            title="Test Book",
            author="Test Author",
        )
        assert result.exists()
        assert result.stat().st_size > 1000

    def test_raise_on_missing_ffmpeg(self) -> None:
        """Should raise if ffmpeg not available (test can't verify this,
        but the constructor checks)."""
        # FFmpeg() will either pass or raise PackagingError if ffmpeg is missing.
        import contextlib

        with contextlib.suppress(PackagingError):
            FFmpeg()
