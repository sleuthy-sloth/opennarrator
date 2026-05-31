"""Tests for the voice manager."""

import pytest

from opennarrator.engines.kokoro import KokoroEngine
from opennarrator.voice.manager import VoiceManager


@pytest.fixture
def manager() -> VoiceManager:
    engine = KokoroEngine(device="mps")
    return VoiceManager(engine)


class TestVoiceManager:
    def test_list_voices(self, manager: VoiceManager) -> None:
        voices = manager.list_voices()
        assert len(voices) >= 5
        names = [v.name for v in voices]
        assert "af_bella" in names
        assert "am_adam" in names

    def test_get_voice_found(self, manager: VoiceManager) -> None:
        voice = manager.get_voice("af_bella")
        assert voice.name == "af_bella"
        assert voice.engine == "kokoro"

    def test_get_voice_not_found(self, manager: VoiceManager) -> None:
        with pytest.raises(KeyError, match="not found"):
            manager.get_voice("nonexistent")

    def test_default_voice_exists(self, manager: VoiceManager) -> None:
        default = manager.default_voice
        assert default in [v.name for v in manager.list_voices()]

    def test_engine_is_accessible(self, manager: VoiceManager) -> None:
        assert manager.engine is not None

    def test_voices_have_descriptions(self, manager: VoiceManager) -> None:
        for v in manager.list_voices():
            assert v.description
            assert "Female" in v.description or "Male" in v.description
