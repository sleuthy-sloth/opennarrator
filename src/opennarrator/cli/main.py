"""Top-level Typer CLI application."""

import typer
from typer.core import TyperGroup

from opennarrator.cli.convert import convert
from opennarrator.cli.preview import preview
from opennarrator.cli.server import server
from opennarrator.cli.voices import info, list_voices


class _NaturalOrderGroup(TyperGroup):
    """Preserve command registration order in --help output."""

    def list_commands(self, ctx):
        return list(self.commands.keys())


app = typer.Typer(
    name="opennarrator",
    help="Open-source audiobook creator — convert ebooks to M4B using open-source TTS engines",
    rich_markup_mode="rich",
    cls=_NaturalOrderGroup,
    invoke_without_command=True,
    no_args_is_help=False,
)

app.command("convert")(convert)
app.command("preview")(preview)
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
def callback(ctx: typer.Context) -> None:
    """OpenNarrator — break the audiobook monopoly.

    Run without arguments to launch the web UI.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand given — launch the web UI directly
        from opennarrator.server.app import run

        run()
