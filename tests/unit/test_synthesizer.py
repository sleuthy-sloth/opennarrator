"""Tests for the synthesizer pipeline stage."""

from pathlib import Path

import pytest

from opennarrator.engines.kokoro import KokoroEngine
from opennarrator.exceptions import SynthesisError
from opennarrator.pipeline.synthesizer import Synthesizer
from opennarrator.types import Chapter


@pytest.fixture
def engine() -> KokoroEngine:
    return KokoroEngine(device="mps")


@pytest.fixture
def chapters() -> list[Chapter]:
    return [
        Chapter(
            index=1,
            title="Chapter One",
            text="This is the first chapter. It has some content for testing.",
        ),
        Chapter(
            index=2, title="Chapter Two", text="This is the second chapter. It continues the story."
        ),
    ]


class TestSynthesizer:
    def test_synthesize_all_chapters(
        self, engine: KokoroEngine, chapters: list[Chapter], tmp_path: Path
    ) -> None:
        synth = Synthesizer(engine=engine, output_dir=tmp_path, voice="af_bella", resume=False)
        paths = synth.synthesize_chapters(chapters)
        assert len(paths) == len(chapters)
        for p in paths:
            assert p.exists()
            assert p.stat().st_size > 1000

    def test_resume_skips_existing(
        self, engine: KokoroEngine, chapters: list[Chapter], tmp_path: Path
    ) -> None:
        # First synthesis
        synth1 = Synthesizer(engine=engine, output_dir=tmp_path, voice="af_bella", resume=True)
        paths1 = synth1.synthesize_chapters(chapters[:1])

        # Second synthesis with resume
        synth2 = Synthesizer(engine=engine, output_dir=tmp_path, voice="af_bella", resume=True)
        paths2 = synth2.synthesize_chapters(chapters)

        # Should have same paths, and the existing file should be untouched
        assert len(paths2) == len(chapters)
        assert paths2[0] == paths1[0]
        assert paths2[0].exists()

    def test_all_existing_skips_synthesis(
        self, engine: KokoroEngine, chapters: list[Chapter], tmp_path: Path
    ) -> None:
        # Pre-create output files
        synth = Synthesizer(engine=engine, output_dir=tmp_path, voice="af_bella", resume=True)
        synth.synthesize_chapters(chapters)

        # Run again — should report all done without re-synthesizing
        paths = synth.synthesize_chapters(chapters)
        assert len(paths) == len(chapters)

    def test_chapter_output_naming(self, engine: KokoroEngine, tmp_path: Path) -> None:
        chapter = Chapter(index=1, title="The Beginning", text="Once upon a time...")
        synth = Synthesizer(engine=engine, output_dir=tmp_path, voice="af_bella")
        path = synth._chapter_path(chapter)
        assert "ch001" in path.name
        assert "The_Beginning" in path.name
        assert path.suffix == ".wav"

    def test_invalid_voice_raises(self, tmp_path: Path) -> None:
        engine = KokoroEngine(device="mps")
        synth = Synthesizer(engine=engine, output_dir=tmp_path, voice="nonexistent")
        chapters = [Chapter(index=1, title="Test", text="Hello.")]
        with pytest.raises(SynthesisError):
            synth.synthesize_chapters(chapters)

    def test_output_dir_created_automatically(
        self, engine: KokoroEngine, chapters: list[Chapter], tmp_path: Path
    ) -> None:
        nested = tmp_path / "deep" / "nested" / "output"
        synth = Synthesizer(engine=engine, output_dir=nested, voice="af_bella")
        paths = synth.synthesize_chapters(chapters[:1])
        assert paths[0].exists()
