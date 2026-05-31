"""Shared type definitions for OpenNarrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Chapter:
    """A single chapter extracted from an ebook."""

    index: int
    """Chapter number (1-based)."""

    title: str
    """Chapter title (e.g. \"Chapter 1\" or \"The Beginning\")."""

    text: str
    """The full body text of this chapter."""


@dataclass
class BookMetadata:
    """Metadata extracted from an ebook file."""

    title: str = "Untitled"
    """Book title."""

    author: str = "Unknown Author"
    """Author name(s)."""

    cover_path: Path | None = None
    """Path to extracted cover image, if any."""

    chapters: list[Chapter] = field(default_factory=list)
    """All detected chapters."""


@dataclass
class Voice:
    """A TTS voice available for synthesis."""

    name: str
    """Unique voice identifier (e.g. \"af_bella\")."""

    engine: str
    """Engine this voice belongs to (e.g. \"kokoro\", \"piper\")."""

    description: str = ""
    """Human-readable description (e.g. \"American English Female — Bella\")."""

    quality_hint: str = "medium"
    """Quality tier hint: \"low\", \"medium\", or \"high\"."""


@dataclass
class ConversionJob:
    """Tracks the state of an audiobook conversion."""

    input_path: Path
    """Source ebook file."""

    output_path: Path
    """Target M4B file."""

    voice: str
    """Selected voice name."""

    status: str = "pending"
    """Current status: pending | extracting | synthesizing | packaging | done | error."""

    total_chapters: int = 0
    """Number of chapters detected."""

    completed_chapters: int = 0
    """Number of chapters synthesized so far."""

    error_message: str = ""
    """Error details if status is \"error\"."""
