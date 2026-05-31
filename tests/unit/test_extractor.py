"""Tests for the EPUB extractor."""

from pathlib import Path

import pytest

from opennarrator.exceptions import ExtractionError
from opennarrator.pipeline.extractor import EpubExtractor, _strip_html


class TestHtmlStripping:
    """_strip_html should clean HTML to plain text."""

    def test_strips_tags(self) -> None:
        result = _strip_html("<p>Hello <b>world</b></p>")
        assert "Hello" in result
        assert "world" in result
        assert "<b>" not in result
        assert "</p>" not in result

    def test_decodes_entities(self) -> None:
        result = _strip_html("&amp; &lt; &gt; &quot; &#39;")
        assert "&" in result
        assert "<" in result
        assert ">" in result
        assert '"' in result
        assert "'" in result

    def test_collapses_newlines(self) -> None:
        result = _strip_html("<p>A</p>\n<p>B</p>\n\n\n\n<p>C</p>")
        assert "A" in result
        assert "B" in result
        assert "C" in result
        # Should have at most double newlines
        assert "\n\n\n" not in result

    def test_handles_empty(self) -> None:
        assert _strip_html("") == ""
        assert _strip_html("<p></p>") == ""


class TestEpubExtractor:
    """Tests with the real sample EPUB."""

    @pytest.fixture
    def sample_epub(self) -> Path:
        return Path("tests/fixtures/sample.epub")

    @pytest.fixture
    def extractor(self) -> EpubExtractor:
        return EpubExtractor()

    def test_extract_returns_book_metadata(
        self, extractor: EpubExtractor, sample_epub: Path
    ) -> None:
        meta = extractor.extract(sample_epub)
        assert meta.title == "A Christmas Carol"
        assert meta.author == "Charles Dickens"
        assert len(meta.chapters) > 0

    def test_extract_has_chapters(self, extractor: EpubExtractor, sample_epub: Path) -> None:
        meta = extractor.extract(sample_epub)
        assert len(meta.chapters) >= 4
        for ch in meta.chapters:
            assert ch.title
            assert len(ch.text) > 200

    def test_chapters_have_content(self, extractor: EpubExtractor, sample_epub: Path) -> None:
        meta = extractor.extract(sample_epub)
        for ch in meta.chapters:
            assert "Scrooge" in ch.text or "Marley" in ch.text or "Spirit" in ch.text

    def test_chapter_indexes_sequential(self, extractor: EpubExtractor, sample_epub: Path) -> None:
        meta = extractor.extract(sample_epub)
        for i, ch in enumerate(meta.chapters, start=1):
            assert ch.index == i

    def test_raises_on_missing_file(self, extractor: EpubExtractor) -> None:
        with pytest.raises(ExtractionError, match="File not found"):
            extractor.extract(Path("/nonexistent/book.epub"))

    def test_raises_on_wrong_format(self, extractor: EpubExtractor, tmp_path: Path) -> None:
        fake = tmp_path / "book.pdf"
        fake.write_text("not an epub")
        with pytest.raises(ExtractionError, match="Expected .epub file"):
            extractor.extract(fake)
