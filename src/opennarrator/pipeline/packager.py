"""M4B packager — orchestrates the final audiobook assembly."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from opennarrator.audio.ffmpeg import FFmpeg
from opennarrator.exceptions import PackagingError
from opennarrator.types import BookMetadata

console = Console()


class Packager:
    """Assembles per-chapter WAV files into a final M4B audiobook.

    1. Trim silence from each chapter WAV
    2. Normalize loudness (EBU R128)
    3. Concatenate into a single audio stream
    4. Encode to AAC with chapter markers, cover art, and metadata
    """

    def __init__(
        self,
        output_path: Path,
        metadata: BookMetadata,
        keep_wavs: bool = False,
    ) -> None:
        self._output = output_path
        self._metadata = metadata
        self._keep_wavs = keep_wavs
        self._ffmpeg = FFmpeg()

    def package(self, chapter_wavs: list[Path]) -> Path:
        """Package chapter WAVs into a final M4B file.

        Args:
            chapter_wavs: List of per-chapter WAV files in order.

        Returns:
            Path to the generated M4B file.

        Raises:
            PackagingError: If any assembly step fails.
        """
        if len(chapter_wavs) != len(self._metadata.chapters):
            raise PackagingError(
                f"Expected {len(self._metadata.chapters)} chapter WAVs, got {len(chapter_wavs)}"
            )

        work_dir = self._output.parent / f".opennarrator_{self._output.stem}"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # ── Step 1: Trim silence ─────────────────────────────────
            trimmed: list[Path] = []
            if len(chapter_wavs) > 1:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    "•",
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task("Trimming silence...", total=len(chapter_wavs))
                    for wav in chapter_wavs:
                        out = work_dir / f"trimmed_{wav.name}"
                        trimmed.append(self._ffmpeg.trim_silence(wav, out))
                        progress.advance(task)
            else:
                trimmed = chapter_wavs

            # ── Step 2: Normalize loudness ───────────────────────────
            normalized: list[Path] = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                "•",
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Normalizing loudness...", total=len(trimmed))
                for wav in trimmed:
                    out = work_dir / f"norm_{wav.name}"
                    normalized.append(self._ffmpeg.normalize_wav(wav, out))
                    progress.advance(task)

            # ── Step 3: Concatenate ──────────────────────────────────
            merged_wav = work_dir / "merged.wav"
            console.print("[dim]Concatenating audio...[/dim]")
            self._ffmpeg.concat_wavs(normalized, merged_wav)

            # ── Step 4: Encode to M4B ────────────────────────────────
            meta = self._metadata
            console.print("[dim]Encoding M4B with chapter markers...[/dim]")
            self._ffmpeg.to_m4b(
                audio_path=merged_wav,
                chapters=meta.chapters,
                output_path=self._output,
                title=meta.title,
                author=meta.author,
                cover_path=meta.cover_path,
            )

            # ── Cleanup ──────────────────────────────────────────────
            if not self._keep_wavs:
                shutil.rmtree(work_dir, ignore_errors=True)

            return self._output

        except (PackagingError, OSError) as exc:
            # Clean up partial output on failure
            if self._output.exists():
                self._output.unlink(missing_ok=True)
            raise PackagingError(f"Audiobook assembly failed: {exc}") from exc
