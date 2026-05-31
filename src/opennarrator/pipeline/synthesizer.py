"""Orchestrates per-chapter TTS synthesis with progress reporting and resume."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from opennarrator.engines.base import BaseTTSEngine
from opennarrator.exceptions import SynthesisError
from opennarrator.types import Chapter

console = Console()


class Synthesizer:
    """Synthesizes chapters into WAV files using a TTS engine.

    Features:
    * Per-chapter progress with Rich progress bars
    * Resume support (skips existing WAV files)
    * Per-chapter subprocess isolation (GPU memory safety)
    """

    def __init__(
        self,
        engine: BaseTTSEngine,
        output_dir: Path,
        voice: str = "af_bella",
        resume: bool = True,
    ) -> None:
        self._engine = engine
        self._output_dir = output_dir
        self._voice = voice
        self._resume = resume

    def synthesize_chapters(
        self,
        chapters: list[Chapter],
        on_progress: None = None,
    ) -> list[Path]:
        """Synthesize all chapters into WAV files.

        Args:
            chapters: Ordered list of chapters to synthesize.

        Returns:
            List of paths to the generated WAV files, one per chapter.

        Raises:
            SynthesisError: If any chapter fails to synthesize
                (after cleaning up partial output).
        """
        output_dir = self._output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        existing_chapters: list[Chapter] = []
        pending_chapters: list[Chapter] = []

        for ch in chapters:
            wav_path = self._chapter_path(ch)
            if self._resume and wav_path.exists() and wav_path.stat().st_size > 0:
                existing_chapters.append(ch)
            else:
                pending_chapters.append(ch)

        # ── Skip info ───────────────────────────────────────────────
        if existing_chapters:
            console.print(
                f"[dim]Resume: {len(existing_chapters)}/{len(chapters)} "
                f"chapters already synthesized, skipping...[/dim]"
            )

        # ── Synthesize pending chapters ─────────────────────────────
        if not pending_chapters:
            console.print("[green]All chapters already synthesized.[/green]")
            return [self._chapter_path(ch) for ch in chapters]

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            "•",
            TimeElapsedColumn(),
            "/",
            TimeRemainingColumn(),
            console=console,
        )

        all_paths: list[Path] = []
        task_id = progress.add_task(
            f"Synthesizing {len(pending_chapters)} chapters...",
            total=len(pending_chapters),
        )

        with progress:
            # Synthesize each pending chapter
            for ch in chapters:
                wav_path = self._chapter_path(ch)

                # Skip already-done chapters
                if self._resume and wav_path.exists() and wav_path.stat().st_size > 0:
                    all_paths.append(wav_path)
                    continue

                chapter_title = ch.title[:50] if ch.title else f"Chapter {ch.index}"
                progress.update(
                    task_id,
                    description=f"[yellow]Chapter {ch.index}[/yellow]: {chapter_title}",
                )

                try:
                    self._engine.synthesize(ch.text, self._voice, wav_path)
                except SynthesisError:
                    # Clean up partial WAV
                    if wav_path.exists():
                        wav_path.unlink(missing_ok=True)
                    raise
                except Exception as exc:
                    if wav_path.exists():
                        wav_path.unlink(missing_ok=True)
                    raise SynthesisError(
                        f"Failed to synthesize chapter {ch.index} ({chapter_title}): {exc}"
                    ) from exc

                all_paths.append(wav_path)
                progress.advance(task_id)

        return [self._chapter_path(ch) for ch in chapters]

    def _chapter_path(self, chapter: Chapter) -> Path:
        """Get the WAV output path for a chapter."""
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in chapter.title
        )
        safe_title = safe_title.strip().replace(" ", "_")[:60]
        return self._output_dir / f"ch{chapter.index:03d}_{safe_title}.wav"
