"""`opennarrator server` — launch the web UI."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()

SERVER_URL: str = ""


def _open_browser() -> None:
    """Open the server URL in the default browser (best-effort, async)."""
    import time
    import urllib.request

    # Wait briefly for the server to be ready
    time.sleep(1.5)
    url = _get_server_url()

    # Quick health check before opening
    try:
        urllib.request.urlopen(f"{url}/api/voices", timeout=3)
    except Exception:
        return  # Server not ready — skip

    try:
        import webbrowser

        webbrowser.open(url)
    except Exception:
        pass


def _get_server_url() -> str:
    global SERVER_URL
    return SERVER_URL


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
    global SERVER_URL
    SERVER_URL = f"http://{host}:{port}"

    console.print("[bold]OpenNarrator Web UI[/bold]")
    console.print(f"  Server: [blue]{SERVER_URL}[/blue]")
    console.print("  Press Ctrl+C to stop.")

    if open_browser:
        import threading

        threading.Thread(target=_open_browser, daemon=True).start()

    try:
        from opennarrator.server.app import run

        run(host=host, port=port)
    except ImportError as exc:
        console.print(
            f"[red]Server dependencies missing:[/red] {exc}\n"
            "Install: [bold]pip install opennarrator[server][/bold]"
        )
        raise typer.Exit(code=1) from exc
