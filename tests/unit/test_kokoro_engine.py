"""Tests for KokoroEngine adapter."""

from pathlib import Path

import pytest

from opennarrator.engines.kokoro import KokoroEngine
from opennarrator.exceptions import SynthesisError


class TestKokoroEngine:
    """Integration-light tests that exercise real Kokoro synthesis."""

    @pytest.fixture
    def engine(self) -> KokoroEngine:
        # Device auto-detected: MPS on macOS, CUDA if available, CPU on CI
        return KokoroEngine()

    def test_list_voices(self, engine: KokoroEngine) -> None:
        voices = engine.list_voices()
        assert len(voices) >= 5
        names = {v.name for v in voices}
        assert "af_bella" in names
        assert "am_adam" in names
        for v in voices:
            assert v.engine == "kokoro"

    def test_synthesize_short_text(self, engine: KokoroEngine, tmp_path: Path) -> None:
        out = engine.synthesize("Hello world.", "af_bella", tmp_path / "test.wav")
        assert out.exists()
        assert out.stat().st_size > 1000  # Should be at least a few KB

    def test_synthesize_longer_text(self, engine: KokoroEngine, tmp_path: Path) -> None:
        text = "This is a slightly longer sentence to test that the Kokoro engine can handle multiple phrases without any issues."
        out = engine.synthesize(text, "af_bella", tmp_path / "long.wav")
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_invalid_voice_raises(self, engine: KokoroEngine, tmp_path: Path) -> None:
        with pytest.raises(SynthesisError, match="Unknown voice"):
            engine.synthesize("Hello", "nonexistent_voice", tmp_path / "bad.wav")

    def test_different_voices_produce_different_output(
        self, engine: KokoroEngine, tmp_path: Path
    ) -> None:
        out1 = engine.synthesize("Hello world.", "af_bella", tmp_path / "v1.wav")
        out2 = engine.synthesize("Hello world.", "af_nicole", tmp_path / "v2.wav")
        # Different voices should produce different byte content
        assert out1.read_bytes() != out2.read_bytes()


class TestKokoroEngineUnit:
    """Pure unit tests (no real synthesis)."""

    def test_engine_default_device_fallback(self) -> None:
        """Engine should init without error, device resolved lazily on first use."""
        engine = KokoroEngine()
        # Device is initially None — resolved when _ensure_loaded() is called
        assert engine._device is None
        engine._ensure_loaded()
        assert engine._device in ("cpu", "mps", "cuda")
