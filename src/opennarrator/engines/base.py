"""Abstract TTS engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from opennarrator.types import Voice


class BaseTTSEngine(ABC):
    """Abstract interface for all TTS engines.

    Subclass this to add support for a new TTS backend (Kokoro, Piper, F5-TTS, etc.).
    """

    @abstractmethod
    def synthesize(self, text: str, voice: str, output_path: Path) -> Path:
        """Synthesize text into a WAV audio file.

        Args:
            text: The text to synthesize.
            voice: Name or identifier of the voice to use.
            output_path: Where to write the resulting WAV file.

        Returns:
            The Path to the generated WAV file.

        Raises:
            SynthesisError: If synthesis fails.
        """
        ...

    @abstractmethod
    def list_voices(self) -> list[Voice]:
        """List all available voices for this engine.

        Returns:
            A list of Voice objects describing available voices.
        """
        ...
