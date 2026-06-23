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

SUPPORTED_INPUT = {".epub", ".txt", ".docx", ".docm"}
SUPPORTED_OUTPUT = {".m4b"}

# Built-in sample passage for the --demo one-shot verification.
_DEMO_TEXT = (
    "It was a bright cold day in April, and the clocks were striking thirteen. "
    "Winston Smith, his chin nuzzled into his breast in an effort to escape the "
    "vile wind, slipped quickly through the glass doors of Victory Mansions, "
    "though not quickly enough to prevent a swirl of gritty dust from entering "
    "along with him. The hallway smelt of boiled cabbage and old rag mats. "
    "At one end of it a coloured poster, too large for indoor display, had been "
    "tacked to the wall. It depicted simply an enormous face, more than a metre "
    "wide: the face of a man of about forty-five, with a heavy black moustache "
    "and ruggedly handsome features. Winston made for the stairs. It was no use "
    "trying the lift. Even at the best of times it was seldom working, and at "
    "present the electric current was cut off during daylight hours. It was part "
    "of the economy drive in preparation for Hate Week. The flat was seven "
    "flights up, and Winston, who was thirty-nine and had a varicose ulcer above "
    "his right ankle, went slowly, resting several times on the way. On each "
    "landing, opposite the lift-shaft, the poster with the enormous face gazed "
    "from the wall. It was one of those pictures which are so contrived that the "
    "eyes follow you about when you move. BIG BROTHER IS WATCHING YOU, the "
    "caption beneath it ran."
)


def _detect_extractor(path: Path):
    """Return the appropriate extractor for the input file."""
    suffix = path.suffix.lower()
    if suffix == ".epub":
        return EpubExtractor()
    elif suffix == ".txt":
        return TxtExtractor()
    elif suffix in (".docx", ".docm"):
        from opennarrator.pipeline.extractor import DocxExtractor  # noqa: PLC0415

        return DocxExtractor()
    else:
        supported = ", ".join(sorted(SUPPORTED_INPUT))
        raise typer.BadParameter(f"Unsupported input format {suffix!r}. Supported: {supported}")


def _run_demo(voice: str, device: str | None, speed: float, keep_wavs: bool) -> None:
    """Synthesize a built-in passage to verify the full pipeline."""
    from opennarrator.pipeline.normalizer import TextNormalizer

    console.print("[bold]OpenNarrator Demo[/bold] — verifying the full pipeline\n")
    console.print(f"  Voice: [cyan]{voice}[/cyan]")
    console.print(f"  Device: [cyan]{device or 'auto'}[/cyan]")
    console.print(f"  Speed: [cyan]{speed}x[/cyan]")
    console.print(f"  Passage: [dim]{len(_DEMO_TEXT)} chars[/dim]\n")

    # ── Normalize ──
    console.print("[bold]Step 1/3:[/bold] Normalizing text...")
    normalizer = TextNormalizer()
    text = normalizer.normalize(_DEMO_TEXT)
    console.print("  [green]✓[/green] Done\n")

    # ── Synthesize ──
    console.print("[bold]Step 2/3:[/bold] Synthesizing speech (this may take a minute)...")
    engine = KokoroEngine(device=device)
    synthesizer = Synthesizer(
        engine=engine,
        output_dir=Path.cwd() / ".opennarrator_demo",
        voice=voice,
        resume=False,
    )
    chapter = type("Chapter", (), {"number": 1, "title": "Demo", "text": text})()
    try:
        wavs = synthesizer.synthesize_chapters([chapter])
    except Exception as exc:
        console.print(f"[red]Synthesis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"  [green]✓[/green] {len(wavs)} WAV file(s)\n")

    # ── Package ──
    output = Path.cwd() / "opennarrator_demo.m4b"
    console.print("[bold]Step 3/3:[/bold] Packaging M4B...")
    metadata = BookMetadata(title="OpenNarrator Demo", author="Demo", chapters=[chapter])
    packager = Packager(output_path=output, metadata=metadata, keep_wavs=keep_wavs)
    try:
        final = packager.package(wavs)
    except Exception as exc:
        console.print(f"[red]Packaging failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    size_mb = final.stat().st_size / (1024 * 1024)
    console.print(f"\n[bold green]✅ Demo complete![/bold green] → {final.name} ({size_mb:.1f} MB)")
    console.print(f"  Open: [blue]open {final}[/blue]")
    console.print(
        "\n[dim]Now try it on a real book: opennarrator convert your-book.epub[/dim]"
    )


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
    device: str | None = typer.Option(
        None,
        "--device",
        "-d",
        help="Compute device (auto-detected if not set: cpu, mps, cuda)",
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
    demo: bool = typer.Option(
        False,
        "--demo",
        help="Synthesize a built-in passage to verify the full pipeline",
    ),
) -> None:
    """Convert an ebook to an M4B audiobook.

    Runs the full pipeline: extract chapters, normalize text,
    synthesize speech with Kokoro TTS, and package into a chaptered M4B.

    Use --demo to test the pipeline with a built-in sample passage
    (no ebook required).
    """
    # ── Demo mode: synthesize built-in passage ──────────────────────
    if demo:
        _run_demo(voice, device, speed, keep_wavs)
        return

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
