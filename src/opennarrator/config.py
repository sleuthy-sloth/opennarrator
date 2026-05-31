"""Configuration management for OpenNarrator.

Settings are loaded from (in priority order):
1. CLI arguments (highest)
2. Environment variables (e.g. ``OPENNARRATOR_VOICE``)
3. Config file at ``~/.config/opennarrator/config.yaml``
4. Defaults (lowest)
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class Settings(BaseSettings):
    """Application-wide configuration for OpenNarrator."""

    model_config = SettingsConfigDict(
        env_prefix="OPENNARRATOR_",
        yaml_file=str(Path.home() / ".config" / "opennarrator" / "config.yaml"),
        extra="ignore",
    )

    # ── Engine ──────────────────────────────────────────────────────
    engine: str = Field(default="kokoro", description="TTS engine to use (kokoro, piper, f5_tts)")
    voice: str = Field(default="af_bella", description="Default voice name")
    device: str = Field(default="mps", description="Compute device (cpu, mps, cuda)")

    # ── Synthesis ────────────────────────────────────────────────────
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
    quality: str = Field(default="high", description="Quality preset (low, medium, high)")

    # ── Paths ────────────────────────────────────────────────────────
    cache_dir: Path = Field(
        default=Path.home() / ".cache" / "opennarrator",
        description="Directory for cached voices and models",
    )
    output_dir: Path = Field(
        default=Path.cwd(),
        description="Default output directory for generated audiobooks",
    )

    # ── Audio ────────────────────────────────────────────────────────
    sample_rate: int = Field(default=24000, description="Output sample rate in Hz")
    loudness_target: float = Field(default=-16.0, description="EBU R128 loudness target (LUFS)")

    # ── Pipeline ─────────────────────────────────────────────────────
    keep_wavs: bool = Field(
        default=False, description="Keep intermediate WAV files after conversion"
    )
    resume: bool = Field(default=True, description="Resume from last completed chapter on restart")

    @classmethod
    def from_yaml(cls, path: Path) -> Settings:
        """Load settings from a YAML file path explicitly."""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    def dump_yaml(self, path: Path) -> None:
        """Write current settings to a YAML file."""
        import yaml

        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Add YAML config file as a settings source."""
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )
