"""`opennarrator convert` — the main audiobook conversion command."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)

from opennarrator.config import Settings
from opennarrator.engines.kokoro import KokoroEngine
from opennarrator.pipeline.extractor import EpubExtractor, TxtExtractor
from opennarrator.pipeline.normalizer import TextNormalizer
from opennarrator.pipeline.packager import Packager
from opennarrator.pipeline.synthesizer import Synthesizer
from opennarrator.types import BookMetadata

console = Console()

SUPPORTED_INPUT = {".epub", ".txt"}
SUPPORTED_OUTPUT = {".m4b"}


def _detect_extractor(path: Path):
    """Return the appropriate extractor for the input file."""
    suffix = path.suffix.lower()
    if suffix == ".epub":
        return EpubExtractor()
    elif suffix == ".txt":
        return TxtExtractor()
    else:
        supported = ", ".join(sorted(SUPPORTED_INPUT))
        raise typer.BadParameter(f"Unsupported input format {suffix!r}. Supported: {supported}")


def convert(
    input_path: Path = typer.Argument(
        ...,
        help="Input ebook file (.epub or .txt)",
        exists=True,
    ),
    voice: str = typer.Option(
        "af_bella",
        "--voice",
        "-v",
        help="TTS voice name",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output .m4b file path",
    ),
    device: str = typer.Option(
        "mps",
        "--device",
        "-d",
        help="Compute device (cpu, mps, cuda)",
    ),
    speed: float = typer.Option(
        1.0,
        "--speed",
        "-s",
        min=0.5,
        max=2.0,
        help="Speech speed multiplier",
    ),
    resume: bool = typer.Option(
        True,
        "--resume/--no-resume",
        help="Resume from last completed chapter",
    ),
    keep_wavs: bool = typer.Option(
        False,
        "--keep-wavs",
        help="Keep intermediate WAV files",
    ),
) -> None:
    """Convert an ebook to an M4B audiobook.

    Runs the full pipeline: extract chapters, normalize text,
    synthesize speech with Kokoro TTS, and package into a chaptered M4B.
    """
    # ── Resolve output path ─────────────────────────────────────────
    if output is None:
        output = input_path.with_suffix(".m4b")
    if output.suffix.lower() not in SUPPORTED_OUTPUT:
        raise typer.BadParameter(f"Output must be one of: {', '.join(sorted(SUPPORTED_OUTPUT))}")

    # ── Step 0: Load settings ────────────────────────────────────────
    settings = Settings()
    voice_to_use = voice or settings.voice
    device_to_use = device or settings.device

    console.print(f"[bold]OpenNarrator[/bold] — converting [cyan]{input_path.name}[/cyan]")

    # ── Step 1: Extract ──────────────────────────────────────────────
    console.print("\n[bold]Step 1/4:[/bold] Extracting chapters...")
    extractor = _detect_extractor(input_path)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Reading ebook...", total=None)
            metadata: BookMetadata = extractor.extract(input_path)
            progress.update(task, completed=True)
    except Exception as exc:
        console.print(f"[red]Extraction failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    total_chapters = len(metadata.chapters)
    console.print(
        f"  [green]✓[/green] {metadata.title} by {metadata.author}"
        f" — {total_chapters} chapter{'s' if total_chapters != 1 else ''}"
    )

    # Normalize text per chapter
    normalizer = TextNormalizer()
    for ch in metadata.chapters:
        ch.text = normalizer.normalize(ch.text)

    # ── Step 2: Synthesize ───────────────────────────────────────────
    console.print(f"\n[bold]Step 2/4:[/bold] Synthesizing speech ([cyan]{voice_to_use}[/cyan])...")

    work_dir = output.parent / f".opennarrator_{output.stem}"
    engine = KokoroEngine(device=device_to_use)
    synthesizer = Synthesizer(
        engine=engine,
        output_dir=work_dir,
        voice=voice_to_use,
        resume=resume,
    )

    try:
        chapter_wavs = synthesizer.synthesize_chapters(metadata.chapters)
    except Exception as exc:
        console.print(f"[red]Synthesis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"  [green]✓[/green] {len(chapter_wavs)} WAV files")

    # ── Step 3: Package ──────────────────────────────────────────────
    console.print("\n[bold]Step 3/4:[/bold] Assembling audiobook...")

    packager = Packager(
        output_path=output,
        metadata=metadata,
        keep_wavs=keep_wavs,
    )

    try:
        final_path = packager.package(chapter_wavs)
    except Exception as exc:
        console.print(f"[red]Assembly failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    # ── Done ─────────────────────────────────────────────────────────
    size_mb = final_path.stat().st_size / (1024 * 1024)
    console.print(
        f"\n[bold green]✅ Done![/bold green] {total_chapters} chapters → {final_path.name} ({size_mb:.1f} MB)"
    )
    console.print(f"  Open in Apple Books: [blue]open {final_path}[/blue]")
