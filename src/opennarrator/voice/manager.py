"""Voice manager — discover, list, and resolve voices across engines.

All download/caching of TTS models is handled automatically by the engine
adapters themselves. The voice manager provides a unified interface for
enumerating available voices and resolving voice names to engine-specific
identifiers.
"""

from __future__ import annotations

from opennarrator.engines.base import BaseTTSEngine
from opennarrator.types import Voice

# Default voice fallback if none configured
_DEFAULT_VOICE = "af_bella"


class VoiceManager:
    """Manages available voices and resolves voice names.

    Wraps a TTS engine's voice list and provides helpers for
    CLI / config integration.
    """

    def __init__(self, engine: BaseTTSEngine) -> None:
        self._engine = engine
        self._voice_map: dict[str, Voice] = {}
        self._refresh()

    def _refresh(self) -> None:
        """Enumerate available voices from the engine."""
        self._voice_map = {v.name: v for v in self._engine.list_voices()}

    def list_voices(self) -> list[Voice]:
        """Return all available voices."""
        return sorted(self._voice_map.values(), key=lambda v: v.name)

    def get_voice(self, name: str) -> Voice:
        """Look up a voice by name.

        Raises:
            KeyError: If the voice is not available.
        """
        if name not in self._voice_map:
            available = ", ".join(sorted(self._voice_map))
            raise KeyError(f"Voice {name!r} not found. Available: {available}")
        return self._voice_map[name]

    @property
    def default_voice(self) -> str:
        """Name of the default voice."""
        if _DEFAULT_VOICE in self._voice_map:
            return _DEFAULT_VOICE
        # Fallback to first available voice
        if self._voice_map:
            return next(iter(self._voice_map))
        return _DEFAULT_VOICE

    @property
    def engine(self) -> BaseTTSEngine:
        """The underlying TTS engine."""
        return self._engine
