"""Top-level Typer CLI application."""

import typer

from opennarrator.cli.convert import convert
from opennarrator.cli.server import server
from opennarrator.cli.voices import info, list_voices

app = typer.Typer(
    name="opennarrator",
    help="Open-source audiobook creator — convert ebooks to M4B using open-source TTS engines",
    rich_markup_mode="rich",
)

app.command("convert")(convert)
app.command("server")(server)

voices_app = typer.Typer(
    name="voices",
    help="List and inspect available TTS voices",
    rich_markup_mode="rich",
)
voices_app.command("list")(list_voices)
voices_app.command("info")(info)
app.add_typer(voices_app)


@app.callback()
def callback() -> None:
    """OpenNarrator — break the audiobook monopoly."""
