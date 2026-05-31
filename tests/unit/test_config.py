"""Tests for the config system."""

import os
from pathlib import Path

from opennarrator.config import Settings


class TestSettingsDefaults:
    """Verify default values are sensible."""

    def test_default_engine(self) -> None:
        s = Settings()
        assert s.engine == "kokoro"

    def test_default_voice(self) -> None:
        s = Settings()
        assert s.voice == "af_bella"

    def test_default_device(self) -> None:
        s = Settings()
        assert s.device == "mps"

    def test_default_speed(self) -> None:
        s = Settings()
        assert s.speed == 1.0

    def test_cache_dir_is_under_home(self) -> None:
        s = Settings()
        assert str(s.cache_dir).startswith(str(Path.home()))


class TestSettingsEnvOverrides:
    """Settings should be overrideable via OPENNARRATOR_* environment variables."""

    def test_env_voice_override(self) -> None:
        os.environ["OPENNARRATOR_VOICE"] = "af_nicole"
        try:
            s = Settings()
            assert s.voice == "af_nicole"
        finally:
            del os.environ["OPENNARRATOR_VOICE"]

    def test_env_engine_override(self) -> None:
        os.environ["OPENNARRATOR_ENGINE"] = "piper"
        try:
            s = Settings()
            assert s.engine == "piper"
        finally:
            del os.environ["OPENNARRATOR_ENGINE"]

    def test_env_device_override(self) -> None:
        os.environ["OPENNARRATOR_DEVICE"] = "cpu"
        try:
            s = Settings()
            assert s.device == "cpu"
        finally:
            del os.environ["OPENNARRATOR_DEVICE"]

    def test_env_speed_override(self) -> None:
        os.environ["OPENNARRATOR_SPEED"] = "0.75"
        try:
            s = Settings()
            assert s.speed == 0.75
        finally:
            del os.environ["OPENNARRATOR_SPEED"]


class TestSettingsYaml:
    """Settings should round-trip through YAML."""

    def test_yaml_round_trip(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "config.yaml"
        original = Settings(voice="af_sarah", engine="kokoro", speed=0.8)
        original.dump_yaml(yaml_path)

        loaded = Settings.from_yaml(yaml_path)
        assert loaded.voice == "af_sarah"
        assert loaded.engine == "kokoro"
        assert loaded.speed == 0.8

    def test_yaml_partial_override(self, tmp_path: Path) -> None:
        """YAML with only a few fields should merge with defaults."""
        yaml_path = tmp_path / "partial.yaml"
        Settings(voice="af_bella").dump_yaml(yaml_path)

        loaded = Settings.from_yaml(yaml_path)
        assert loaded.voice == "af_bella"
        # Other fields should still be defaults
        assert loaded.engine == "kokoro"
        assert loaded.speed == 1.0


class TestSettingsValidation:
    """Field constraints should be enforced."""

    def test_speed_too_low(self) -> None:
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(speed=-1.0)

    def test_speed_too_high(self) -> None:
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(speed=3.0)

    def test_speed_zero(self) -> None:
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(speed=0.0)
