"""Kokoro TTS engine adapter.

Kokoro (hexgrad/Kokoro-82M) is an Apache 2.0 licensed TTS model that runs
efficiently on CPU and MPS. Voices are bundled in the model weights —
downloaded automatically on first use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from opennarrator.engines.base import BaseTTSEngine
from opennarrator.exceptions import SynthesisError
from opennarrator.types import Voice

SAMPLE_RATE = 24000

# Voices known to work with Kokoro-82M. Bundled in model weights.
_KNOWN_VOICES: dict[str, str] = {
    # American English Female
    "af_bella": "American English Female — Bella",
    "af_nicole": "American English Female — Nicole",
    "af_sarah": "American English Female — Sarah",
    "af_sky": "American English Female — Sky",
    "af_alloy": "American English Female — Alloy",
    "af_aoede": "American English Female — Aoede",
    "af_heart": "American English Female — Heart",
    "af_nova": "American English Female — Nova",
    # American English Male
    "am_adam": "American English Male — Adam",
    "am_michael": "American English Male — Michael",
    "am_onyx": "American English Male — Onyx",
    "am_puck": "American English Male — Puck",
    # British English Female
    "bf_emma": "British English Female — Emma",
    "bf_isabella": "British English Female — Isabella",
    # British English Male
    "bm_george": "British English Male — George",
    "bm_lewis": "British English Male — Lewis",
}


class KokoroEngine(BaseTTSEngine):
    """TTS engine adapter for Kokoro (hexgrad/Kokoro-82M).

    Downloads the model from HuggingFace on first instantiation.
    Voices are bundled — no separate download needed.
    """

    def __init__(self, device: str | None = None) -> None:
        self._device = device  # Resolved lazily when torch is imported
        self._pipeline: Any = None
        self._model: Any = None
        self._loaded: bool = False

    @staticmethod
    def _resolve_device(device: str | None = None) -> str:
        """Determine best available compute device.

        Import torch lazily — this module may be imported without
        torch installed (e.g. for CLI help or voice listing).
        """
        import torch  # noqa: PLC0415

        if device:
            return device
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _ensure_loaded(self) -> None:
        """Lazy-load the Kokoro pipeline and model."""
        if self._loaded:
            return

        # Resolve device on first use
        if self._device is None:
            self._device = self._resolve_device()

        try:
            from kokoro import KPipeline  # noqa: PLC0415

            self._pipeline = KPipeline(lang_code="a", device=self._device)
            self._loaded = True
        except ImportError as exc:
            raise SynthesisError(
                "Kokoro is not installed. Run: pip install opennarrator[kokoro]"
            ) from exc
        except Exception as exc:
            raise SynthesisError(f"Failed to load Kokoro model: {exc}") from exc

    def synthesize(
        self, text: str, voice: str, output_path: Path, speed: float = 1.0
    ) -> Path:
        """Synthesize text into a WAV file using Kokoro.

        Args:
            text: Text to synthesize.
            voice: Voice name (e.g. ``af_bella``).
            output_path: Destination WAV path.
            speed: Speech speed multiplier (0.5-2.0).

        Returns:
            The path to the generated WAV file.

        Raises:
            SynthesisError: If synthesis or model loading fails,
                or if the voice name is unknown.
        """
        self._ensure_loaded()
        pipeline = self._pipeline

        # Validate voice
        if voice not in _KNOWN_VOICES:
            available = ", ".join(sorted(_KNOWN_VOICES))
            raise SynthesisError(f"Unknown voice {voice!r}. Available: {available}")

        audio_chunks: list[Any] = []

        try:
            for result in pipeline(text, voice=voice, speed=speed):
                if result is not None and hasattr(result, "audio"):
                    chunk = result.audio.cpu().numpy()
                    audio_chunks.append(chunk)
        except Exception as exc:
            raise SynthesisError(f"Kokoro synthesis failed: {exc}") from exc

        if not audio_chunks:
            raise SynthesisError("Kokoro produced no audio output")

        full_audio = np.concatenate(audio_chunks)

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(output_path), full_audio, SAMPLE_RATE)
        except OSError as exc:
            raise SynthesisError(
                f"Failed to write WAV to {output_path}: {exc}"
            ) from exc

        return output_path

    def list_voices(self) -> list[Voice]:
        """List all known Kokoro voices."""
        return [
            Voice(name=name, engine="kokoro", description=desc, quality_hint="high")
            for name, desc in _KNOWN_VOICES.items()
        ]
