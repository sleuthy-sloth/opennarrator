"""Voice registry — cached listing of installed voices.

Provides factory helpers to create a VoiceManager for a given engine,
and a shorthand to list or resolve voices.
"""

from __future__ import annotations

from opennarrator.engines.base import BaseTTSEngine
from opennarrator.voice.manager import VoiceManager


def create_voice_manager(engine: BaseTTSEngine) -> VoiceManager:
    """Create a VoiceManager for the given engine.

    The engine handles all model download/caching on first use.
    """
    return VoiceManager(engine)
