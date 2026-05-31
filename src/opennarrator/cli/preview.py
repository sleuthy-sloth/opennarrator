"""`opennarrator preview` — generate and play a voice sample."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.text import Text

from opennarrator.engines.kokoro import KokoroEngine

console = Console()

_PREVIEW_TEXT = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife. "
    '"My dear Mr. Bennet," said his lady to him one day, "have you heard '
    'that Netherfield Park is let at last?"'
)


def preview(
    voice: str = typer.Argument(
        ...,
        help="Voice name to preview (e.g. af_bella)",
    ),
    device: str = typer.Option(
        "mps",
        "--device",
        "-d",
        help="Compute device (cpu, mps, cuda)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Save sample to a file instead of playing",
    ),
) -> None:
    """Preview a TTS voice with a standard sample passage.

    Generates a ~10-second sample and plays it (or saves to a file).
    """
    preview_dir = Path.home() / ".opennarrator" / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    if output is None:
        output = preview_dir / f"{voice}_preview.wav"

    console.print(f"[bold]Generating preview[/bold] for voice [cyan]{voice}[/cyan]...")
    console.print(Text(_PREVIEW_TEXT, style="dim italic"))

    engine = KokoroEngine(device=device)
    try:
        engine.synthesize(_PREVIEW_TEXT, voice, output)
    except Exception as exc:
        console.print(f"[red]Preview failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    duration = output.stat().st_size / (24000 * 2)  # rough estimate
    size_kb = output.stat().st_size / 1024
    console.print(f"  [green]✓[/green] {size_kb:.0f} KB sample ({duration:.0f}s)")

    if output.parent == preview_dir and output.suffix == ".wav":
        import subprocess as sp

        try:
            sp.run(["open", str(output)], check=False)
        except Exception:
            console.print(f"  Sample saved to: {output}")
