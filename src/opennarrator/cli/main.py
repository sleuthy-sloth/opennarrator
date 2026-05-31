"""Top-level Typer CLI application."""

import typer

app = typer.Typer(
    name="opennarrator",
    help="Open-source audiobook creator — convert ebooks to M4B using open-source TTS engines",
    rich_markup_mode="rich",
)


@app.callback()
def callback() -> None:
    """OpenNarrator — break the audiobook monopoly."""
