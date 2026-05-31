"""ffmpeg subprocess wrapper — audio processing and M4B packaging."""

from __future__ import annotations

import subprocess
from pathlib import Path

from opennarrator.exceptions import PackagingError
from opennarrator.types import Chapter

SAMPLE_RATE = 24000
"""Target sample rate matching Kokoro output."""

AAC_BITRATE = "96k"
"""AAC encoding bitrate. 96k is a good balance for speech."""

LOUDNESS_TARGET = -16.0
"""EBU R128 integrated loudness target (LUFS)."""


def _check_ffmpeg() -> None:
    """Verify ffmpeg is installed and available."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise PackagingError(
            "ffmpeg is required but not found. Install it:\n"
            "  macOS: brew install ffmpeg\n"
            "  Linux: sudo apt install ffmpeg"
        ) from exc


def _write_file_list(paths: list[Path], list_path: Path) -> None:
    """Write a concat demuxer file list."""
    lines = [f"file '{p.resolve()}'\n" for p in paths]
    list_path.write_text("".join(lines))


def _write_chapter_metadata(
    chapters: list[Chapter],
    total_duration_seconds: float,
) -> str:
    """Generate ffmetadata chapter section.

    Each chapter needs START/END timestamps in milliseconds and a title.
    """
    lines = [";FFMETADATA1\n"]
    current_seconds = 0.0

    # Estimate duration per chapter proportionally (all chapters have
    # approximately the same narration speed). A better approach would
    # be to measure actual WAV durations, but this works well enough
    # for the metadata header.
    total_chars = sum(len(ch.text) for ch in chapters)
    if total_chars == 0:
        total_chars = 1  # avoid division by zero

    for ch in chapters:
        # Estimate this chapter's duration from its text proportion
        char_fraction = len(ch.text) / total_chars
        chapter_duration = total_duration_seconds * char_fraction
        start_ms = int(current_seconds * 1000)
        end_ms = int((current_seconds + chapter_duration) * 1000)

        lines.append("[CHAPTER]\n")
        lines.append("TIMEBASE=1/1000\n")
        lines.append(f"START={start_ms}\n")
        lines.append(f"END={end_ms}\n")
        lines.append(f"title={ch.title}\n")
        lines.append("\n")

        current_seconds += chapter_duration

    return "".join(lines)


class FFmpeg:
    """High-level ffmpeg wrapper for audiobook assembly."""

    def __init__(self) -> None:
        _check_ffmpeg()

    @staticmethod
    def normalize_wav(input_path: Path, output_path: Path) -> Path:
        """Apply EBU R128 loudness normalization to a WAV file.

        Uses a single-pass loudnorm filter. For production-quality
        output, a two-pass approach (measure then apply) would be
        more accurate, but single-pass is sufficient for v0.1.
        """
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-af",
            (
                f"loudnorm=I={LOUDNESS_TARGET}:LRA=11:TP=-1.5:"
                f"measured_I={LOUDNESS_TARGET}:measured_LRA=11:"
                f"measured_TP=-1.5:measured_thresh=-30:offset=0"
            ),
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-f",
            "wav",
            str(output_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise PackagingError(
                    f"loudnorm failed for {input_path.name}: {result.stderr[:200]}"
                )
        except OSError as exc:
            raise PackagingError(f"ffmpeg error: {exc}") from exc

        return output_path

    @staticmethod
    def concat_wavs(wav_paths: list[Path], output_path: Path) -> Path:
        """Concatenate multiple WAV files into a single WAV.

        Uses ffmpeg's concat demuxer for fast stream copy.
        """
        list_file = output_path.with_suffix(".list.txt")
        _write_file_list(wav_paths, list_file)

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            str(output_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise PackagingError(f"concat failed: {result.stderr[:200]}")
        except OSError as exc:
            raise PackagingError(f"ffmpeg error: {exc}") from exc
        finally:
            list_file.unlink(missing_ok=True)

        return output_path

    @staticmethod
    def get_duration(wav_path: Path) -> float:
        """Get audio duration in seconds using ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(wav_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return float(result.stdout.strip())
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            raise PackagingError(f"Failed to get duration for {wav_path}: {exc}") from exc

    @staticmethod
    def trim_silence(input_path: Path, output_path: Path) -> Path:
        """Remove leading and trailing silence from a WAV file."""
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-af",
            "silenceremove=start_periods=1:start_duration=0.25:"
            "start_threshold=-50dB:detection=peak,"
            "areverse,silenceremove=start_periods=1:start_duration=0.25:"
            "start_threshold=-50dB:detection=peak,areverse",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-f",
            "wav",
            str(output_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                # Non-critical — fall back to input
                return input_path
        except OSError:
            return input_path

        return output_path if output_path.exists() else input_path

    @staticmethod
    def to_m4b(
        audio_path: Path,
        chapters: list[Chapter],
        output_path: Path,
        title: str = "Untitled",
        author: str = "Unknown Author",
        cover_path: Path | None = None,
    ) -> Path:
        """Encode a WAV file to M4B with chapter markers and metadata.

        Args:
            audio_path: Path to the merged WAV file.
            chapters: List of chapters with titles.
            output_path: Destination .m4b file.
            title: Book title for metadata.
            author: Book author for metadata.
            cover_path: Optional path to cover art image.

        Returns:
            The output M4B file path.
        """
        duration = FFmpeg.get_duration(audio_path)
        metadata = _write_chapter_metadata(chapters, duration)
        metadata_path = output_path.with_suffix(".metadata.txt")
        metadata_path.write_text(metadata)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(audio_path),
            "-i",
            str(metadata_path),
            "-map_metadata",
            "1",
            "-c:a",
            "aac",
            "-b:a",
            AAC_BITRATE,
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-metadata",
            f"title={title}",
            "-metadata",
            f"artist={author}",
            "-metadata",
            "genre=Audiobook",
            "-movflags",
            "+faststart",
        ]

        if cover_path and cover_path.exists():
            cmd.extend(
                [
                    "-i",
                    str(cover_path),
                    "-map",
                    "0",
                    "-map",
                    "2",
                    "-c:v",
                    "mjpeg",
                    "-disposition:v:0",
                    "attached_pic",
                ]
            )
        else:
            cmd.extend(["-map", "0"])

        cmd.append(str(output_path))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise PackagingError(f"M4B encoding failed: {result.stderr[:300]}")
        except OSError as exc:
            raise PackagingError(f"ffmpeg error: {exc}") from exc
        finally:
            metadata_path.unlink(missing_ok=True)

        if not output_path.exists():
            raise PackagingError(f"M4B output was not created at {output_path}")

        return output_path
