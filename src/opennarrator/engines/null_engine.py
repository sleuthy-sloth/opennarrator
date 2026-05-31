"""Null engine — outputs silence. Useful for testing the pipeline."""

from __future__ import annotations

import struct
import wave
from pathlib import Path

from opennarrator.engines.base import BaseTTSEngine
from opennarrator.exceptions import SynthesisError
from opennarrator.types import Voice

SAMPLE_RATE = 24000
SILENCE_DURATION_SECONDS = 1.0
NUM_CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM


class NullEngine(BaseTTSEngine):
    """A TTS engine that produces silence.

    Every ``synthesize()`` call writes a WAV file containing 1 second of
    silence. Useful for validating pipeline architecture without a real
    TTS dependency.
    """

    def synthesize(self, text: str, voice: str, output_path: Path) -> Path:
        """Write a silent WAV file."""
        num_samples = int(SAMPLE_RATE * SILENCE_DURATION_SECONDS)

        try:
            with wave.open(str(output_path), "wb") as wav_file:
                wav_file.setnchannels(NUM_CHANNELS)
                wav_file.setsampwidth(SAMPLE_WIDTH)
                wav_file.setframerate(SAMPLE_RATE)
                for _ in range(num_samples):
                    wav_file.writeframes(struct.pack("<h", 0))
        except (OSError, wave.Error) as exc:
            raise SynthesisError(f"Failed to write silent WAV to {output_path}: {exc}") from exc

        return output_path

    def list_voices(self) -> list[Voice]:
        """Return a single placeholder voice."""
        return [
            Voice(
                name="silence",
                engine="null",
                description="Silence — 1 second of audio per call",
                quality_hint="low",
            ),
        ]
