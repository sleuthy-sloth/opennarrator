"""FastAPI application for the OpenNarrator web UI."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from opennarrator.cli.convert import _detect_extractor
from opennarrator.engines.kokoro import KokoroEngine
from opennarrator.pipeline.normalizer import TextNormalizer
from opennarrator.pipeline.packager import Packager
from opennarrator.types import BookMetadata
from opennarrator.voice.manager import VoiceManager

# ── In-memory job store ─────────────────────────────────────────────────

jobs: dict[str, dict[str, Any]] = {}
# Each job can have an asyncio.Event that progress reporters set
# when they push an update, and a list of pending events.
_job_events: dict[str, asyncio.Queue[str]] = {}


def _job_dir(job_id: str) -> Path:
    return Path.home() / ".opennarrator" / "jobs" / job_id


def _output_path(job_id: str) -> Path:
    return Path.home() / ".opennarrator" / "output" / f"{job_id}.m4b"


def _create_job(input_path: Path, voice: str, device: str) -> str:
    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "id": job_id,
        "input_file": input_path.name,
        "voice": voice,
        "device": device,
        "status": "queued",
        "progress": 0.0,
        "message": "Waiting to start...",
        "chapters_total": 0,
        "chapters_completed": 0,
        "output_file": None,
        "error": None,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _job_events[job_id] = asyncio.Queue()
    return job_id


def _update_job(job_id: str, **kwargs: Any) -> None:
    if job_id in jobs:
        jobs[job_id].update(kwargs)
        # Push update to SSE queue
        queue = _job_events.get(job_id)
        if queue:
            update = {k: jobs[job_id][k] for k in kwargs}
            update["type"] = "progress"
            queue.put_nowait(json.dumps(update))


async def _run_conversion(
    job_id: str, input_path: Path, voice: str, device: str, speed: float = 1.0
) -> None:
    """Run the full conversion pipeline with progress updates."""
    try:
        _update_job(job_id, status="extracting", message="Reading ebook...")

        extractor = _detect_extractor(input_path)
        metadata: BookMetadata = extractor.extract(input_path)
        total_chapters = len(metadata.chapters)

        _update_job(
            job_id,
            status="extracting",
            message=f"Found {total_chapters} chapters",
            chapters_total=total_chapters,
        )

        normalizer = TextNormalizer()
        for ch in metadata.chapters:
            ch.text = normalizer.normalize(ch.text)

        # ── Synthesize ───────────────────────────────────────────────
        _update_job(job_id, status="synthesizing", message="Loading TTS engine...")

        work_dir = _job_dir(job_id) / "wavs"
        engine = KokoroEngine(device=device)

        # Patch synthesizer to send progress per chapter
        chapter_wavs: list[Path] = []
        for i, ch in enumerate(metadata.chapters):
            _update_job(
                job_id,
                status="synthesizing",
                message=f"Chapter {ch.index}: {ch.title[:50]}",
                chapters_completed=i,
                progress=(i / total_chapters) * 80,  # 0-80% for synthesis
            )
            out_path = work_dir / f"ch{i + 1:03d}.wav"
            engine.synthesize(ch.text, voice, out_path, speed=speed)
            chapter_wavs.append(out_path)

        _update_job(
            job_id,
            status="packaging",
            message="Assembling audiobook...",
            chapters_completed=total_chapters,
            progress=80,
        )

        # ── Package ──────────────────────────────────────────────────
        output_path = _output_path(job_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        packager = Packager(
            output_path=output_path,
            metadata=metadata,
            keep_wavs=False,
        )
        packager.package(chapter_wavs)

        _update_job(
            job_id,
            status="done",
            message="Conversion complete!",
            progress=100,
            output_file=str(output_path),
        )

    except Exception as exc:
        _update_job(
            job_id,
            status="error",
            message=str(exc),
            error=str(exc),
        )


# ── FastAPI app ─────────────────────────────────────────────────────────

app = FastAPI(
    title="OpenNarrator",
    description="Open-source audiobook creator",
    version="0.1.0",
)

# Serve static frontend
HERE = Path(__file__).parent
STATIC_DIR = HERE / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


# ── API Routes ──────────────────────────────────────────────────────────


@app.post("/api/convert")
async def api_convert(request: Request) -> JSONResponse:
    """Start a conversion job. Accepts multipart file upload + voice/device params."""
    form = await request.form()
    file = form.get("file")
    voice = str(form.get("voice", "af_bella"))
    device = str(form.get("device", "mps"))

    if not file or not hasattr(file, "filename") or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Save uploaded file
    upload_dir = Path.home() / ".opennarrator" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    input_path = upload_dir / str(file.filename)

    content = await file.read()
    input_path.write_bytes(content)

    # Speed is passed as a form field
    speed = float(str(form.get("speed", "1.0")))

    job_id = _create_job(input_path, voice, device)
    asyncio.create_task(_run_conversion(job_id, input_path, voice, device, speed=speed))

    return JSONResponse({"job_id": job_id})


@app.get("/api/jobs")
async def api_list_jobs() -> JSONResponse:
    """List all conversion jobs."""
    return JSONResponse(
        [
            {
                "id": j["id"],
                "input_file": j["input_file"],
                "voice": j["voice"],
                "status": j["status"],
                "progress": j["progress"],
                "message": j["message"],
                "created_at": j["created_at"],
            }
            for j in jobs.values()
        ]
    )


@app.get("/api/jobs/{job_id}")
async def api_job_status(job_id: str) -> JSONResponse:
    """Get the status of a specific job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse(job)


@app.get("/api/jobs/{job_id}/stream")
async def api_job_stream(job_id: str) -> EventSourceResponse:
    """SSE stream of job progress updates."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        queue = _job_events.get(job_id)
        if not queue:
            return

        # Send current state immediately
        yield {"event": "progress", "data": json.dumps(jobs[job_id])}

        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=30)
                yield {"event": "progress", "data": data}

                # If job is terminal, close the stream
                job = jobs.get(job_id)
                if job and job["status"] in ("done", "error"):
                    yield {"event": "done", "data": data}
                    return
            except TimeoutError:
                # Keep-alive
                yield {"event": "keepalive", "data": ""}

    return EventSourceResponse(event_generator())


@app.get("/api/download/{job_id}")
async def api_download(job_id: str) -> FileResponse:
    """Download the finished M4B file."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done" or not job["output_file"]:
        raise HTTPException(status_code=400, detail="Job not complete")

    output_path = Path(job["output_file"])
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        str(output_path),
        media_type="audio/mp4",
        filename=job["input_file"].rsplit(".", 1)[0] + ".m4b",
    )


@app.get("/api/voices")
async def api_voices() -> JSONResponse:
    """List available TTS voices."""
    engine = KokoroEngine(device="mps")
    manager = VoiceManager(engine)
    return JSONResponse(
        [
            {"name": v.name, "description": v.description, "engine": v.engine}
            for v in manager.list_voices()
        ]
    )


_PREVIEW_CACHE: dict[str, Path] = {}
_PREVIEW_TEXT = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife. "
    '"My dear Mr. Bennet," said his lady to him one day, "have you heard '
    'that Netherfield Park is let at last?"'
)


@app.get("/api/preview/{voice_name}")
async def api_preview(voice_name: str) -> FileResponse:
    """Generate and serve a short voice preview sample."""
    cache_dir = Path.home() / ".opennarrator" / "previews"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{voice_name}.wav"

    if cached.exists():
        return FileResponse(str(cached), media_type="audio/wav")

    # Generate the preview sample
    engine = KokoroEngine(device="mps")
    try:
        engine.synthesize(_PREVIEW_TEXT, voice_name, cached)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Voice {voice_name!r} not available",
        ) from exc

    return FileResponse(str(cached), media_type="audio/wav")


@app.delete("/api/previews/clear")
async def api_clear_previews() -> JSONResponse:
    """Clear the voice preview cache."""
    cache_dir = Path.home() / ".opennarrator" / "previews"
    if cache_dir.exists():
        import shutil

        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
    return JSONResponse({"ok": True, "cleared": True})


# ── Serve Frontend ──────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the main SPA frontend."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>OpenNarrator Web UI</h1><p>Frontend not found.</p>")


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Start the uvicorn server.

    Port is overridden by the PORT environment variable (used by Hugging
    Face Spaces and other cloud platforms).
    """
    import os

    # Allow PORT env var override (HF Spaces, Render, Fly.io)
    env_port = os.environ.get("PORT")
    if env_port:
        try:
            port = int(env_port)
        except (ValueError, TypeError):
            pass

    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")
