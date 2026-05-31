"""Tests for the TXT extractor."""

from pathlib import Path

import pytest

from opennarrator.exceptions import ExtractionError
from opennarrator.pipeline.extractor import TxtExtractor


class TestTxtExtractor:
    """Tests for plain text chapter extraction."""

    @pytest.fixture
    def extractor(self) -> TxtExtractor:
        return TxtExtractor()

    def test_detects_chapter_1_format(self, extractor: TxtExtractor, tmp_path: Path) -> None:
        text = """Some preamble text.
Chapter 1
This is the first chapter content.
Chapter 2
This is the second chapter content.
"""
        path = tmp_path / "test.txt"
        path.write_text(text)
        meta = extractor.extract(path)
        assert len(meta.chapters) == 2
        assert meta.chapters[0].title == "Chapter 1"
        assert meta.chapters[1].title == "Chapter 2"

    def test_detects_roman_numeral_chapter(self, extractor: TxtExtractor, tmp_path: Path) -> None:
        text = """CHAPTER I
The first chapter begins here.
CHAPTER II
The second chapter begins here.
"""
        path = tmp_path / "roman.txt"
        path.write_text(text)
        meta = extractor.extract(path)
        assert len(meta.chapters) >= 2
        assert meta.chapters[0].title == "CHAPTER I"

    def test_detects_stave_format(self, extractor: TxtExtractor, tmp_path: Path) -> None:
        text = """Preface text here.
STAVE ONE: Marley's Ghost
The first stave begins.
STAVE TWO: The First of the Three Spirits
The second stave begins.
"""
        path = tmp_path / "stave.txt"
        path.write_text(text)
        meta = extractor.extract(path)
        assert len(meta.chapters) == 2
        assert "STAVE ONE" in meta.chapters[0].title

    def test_no_chapters_fallback(self, extractor: TxtExtractor, tmp_path: Path) -> None:
        text = "This is a plain text file with no chapter headings at all. It should be treated as one single chapter for the entire book content."
        path = tmp_path / "plain.txt"
        path.write_text(text)
        meta = extractor.extract(path)
        assert len(meta.chapters) == 1
        assert meta.chapters[0].title == "Chapter 1"

    def test_empty_file_raises(self, extractor: TxtExtractor, tmp_path: Path) -> None:
        path = tmp_path / "empty.txt"
        path.write_text("")
        with pytest.raises(ExtractionError, match="No chapters found"):
            extractor.extract(path)

    def test_raises_on_missing_file(self, extractor: TxtExtractor) -> None:
        with pytest.raises(ExtractionError, match="File not found"):
            extractor.extract(Path("/nonexistent/book.txt"))
