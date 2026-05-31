"""`opennarrator voices` — voice listing and information."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from opennarrator.engines.kokoro import KokoroEngine
from opennarrator.voice.manager import VoiceManager

console = Console()


def _get_manager() -> VoiceManager:
    """Create a voice manager from the default Kokoro engine.

    The model is downloaded lazily on first engine use, so this is fast
    unless it's the very first invocation.
    """
    engine = KokoroEngine(device="mps")
    return VoiceManager(engine)


def list_voices(
    engine: str = typer.Option(
        "kokoro",
        "--engine",
        "-e",
        help="TTS engine to list voices for",
    ),
) -> None:
    """List all available TTS voices."""
    manager = _get_manager()
    voices = manager.list_voices()

    if not voices:
        console.print("[yellow]No voices found.[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Available Voices ({engine})")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description")
    table.add_column("Engine", style="dim")
    table.add_column("Quality")

    for voice in voices:
        table.add_row(
            voice.name,
            voice.description,
            voice.engine,
            voice.quality_hint,
        )

    console.print(table)
    console.print(f"\n[dim]Default voice: [cyan]{manager.default_voice}[/cyan][/dim]")


def info(
    voice_name: str = typer.Argument(
        ...,
        help="Voice name (e.g. af_bella)",
    ),
) -> None:
    """Show details about a specific voice."""
    manager = _get_manager()

    try:
        voice = manager.get_voice(voice_name)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold]Voice:[/bold] [cyan]{voice.name}[/cyan]")
    console.print(f"  Description: {voice.description}")
    console.print(f"  Engine:      {voice.engine}")
    console.print(f"  Quality:     {voice.quality_hint}")
    console.print(f"\n[dim]Use: opennarrator convert book.epub --voice {voice.name}[/dim]")
