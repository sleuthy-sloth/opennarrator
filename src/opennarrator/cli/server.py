"""`opennarrator server` — launch the web UI."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def server(
    port: int = typer.Option(
        8080,
        "--port",
        "-p",
        help="Port to serve on",
        min=1024,
        max=65535,
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind to",
    ),
    open_browser: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open browser on start",
    ),
) -> None:
    """Launch the OpenNarrator web interface.

    Starts a FastAPI server with a drag-and-drop web UI for converting
    ebooks to audiobooks. Open http://localhost:{port} in your browser.
    """
    console.print("[bold]OpenNarrator Web UI[/bold]")
    console.print(f"  Server: [blue]http://{host}:{port}[/blue]")
    console.print("  Press Ctrl+C to stop.")

    if open_browser:
        import webbrowser

        webbrowser.open(f"http://{host}:{port}")

    try:
        from opennarrator.server.app import run

        run(host=host, port=port)
    except ImportError as exc:
        console.print(
            f"[red]Server dependencies missing:[/red] {exc}\n"
            "Install: [bold]pip install opennarrator[server][/bold]"
        )
        raise typer.Exit(code=1) from exc
