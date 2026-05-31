"""Tests for the M4B packager."""

import math
import wave
from pathlib import Path

import pytest

from opennarrator.exceptions import PackagingError
from opennarrator.pipeline.packager import Packager
from opennarrator.types import BookMetadata, Chapter


def _make_wav(path: Path, duration: float = 2.0, freq: float = 440) -> None:
    """Generate a simple sine-wave WAV file for testing."""
    import struct

    sample_rate = 24000
    num_samples = int(sample_rate * duration)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for n in range(num_samples):
            value = int(32767 * 0.3 * math.sin(n / sample_rate * freq * 6.28))
            wf.writeframes(struct.pack("<h", value))


@pytest.fixture
def metadata() -> BookMetadata:
    return BookMetadata(
        title="Test Book",
        author="Test Author",
        chapters=[
            Chapter(index=1, title="Chapter 1", text="First chapter content here."),
            Chapter(index=2, title="Chapter 2", text="Second chapter content here."),
        ],
    )


@pytest.fixture
def chapter_wavs(metadata: BookMetadata, tmp_path: Path) -> list[Path]:
    wavs = []
    for ch in metadata.chapters:
        p = tmp_path / f"ch{ch.index:03d}_{ch.title.replace(' ', '_')}.wav"
        _make_wav(p, duration=2.0)
        wavs.append(p)
    return wavs


class TestPackager:
    def test_package_creates_m4b(
        self, metadata: BookMetadata, chapter_wavs: list[Path], tmp_path: Path
    ) -> None:
        out = tmp_path / "output.m4b"
        packager = Packager(output_path=out, metadata=metadata, keep_wavs=False)
        result = packager.package(chapter_wavs)
        assert result.exists()
        assert result.suffix == ".m4b"
        assert result.stat().st_size > 1000

    def test_package_with_cover(
        self, metadata: BookMetadata, chapter_wavs: list[Path], tmp_path: Path
    ) -> None:
        # Generate a valid JPEG cover using ffmpeg
        import subprocess

        cover = tmp_path / "cover.jpg"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=64x64:d=1",
                "-frames:v",
                "1",
                str(cover),
            ],
            capture_output=True,
            check=True,
        )
        metadata.cover_path = cover

    def test_mismatched_chapter_count_raises(self, metadata: BookMetadata, tmp_path: Path) -> None:
        packager = Packager(output_path=tmp_path / "bad.m4b", metadata=metadata)
        # Pass wrong number of WAVs
        with pytest.raises(PackagingError, match="Expected"):
            packager.package([tmp_path / "missing.wav"])

    def test_package_cleans_up_on_failure(self, metadata: BookMetadata, tmp_path: Path) -> None:
        out = tmp_path / "fail.m4b"
        packager = Packager(output_path=out, metadata=metadata)
        # Pass non-existent WAVs
        bad_wavs = [tmp_path / "nonexistent.wav"]
        with pytest.raises(PackagingError):
            packager.package(bad_wavs)
        # Output should not exist on failure
        assert not out.exists()
