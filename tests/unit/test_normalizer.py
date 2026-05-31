"""Tests for the text normalizer."""

from opennarrator.pipeline.normalizer import TextNormalizer


class TestNumberExpansion:
    """Numbers should be converted to spoken-word forms."""

    def setup_method(self) -> None:
        self.n = TextNormalizer()

    def test_small_number(self) -> None:
        assert self.n.normalize("I have 42 cats") == "I have forty two cats"

    def test_single_digit(self) -> None:
        assert self.n.normalize("3 little pigs") == "three little pigs"

    def test_zero(self) -> None:
        assert self.n.normalize("zero 0") == "zero zero"

    def test_large_number_preserved(self) -> None:
        assert self.n.normalize("ID 99999") == "ID 99999"

    def test_hundreds(self) -> None:
        result = self.n.normalize("page 142")
        assert "one hundred forty two" in result

    def test_multiple_numbers(self) -> None:
        result = self.n.normalize("chapter 1 verse 2")
        assert "chapter one verse two" in result


class TestQuoteNormalization:
    """Smart/curly quotes should become straight."""

    def setup_method(self) -> None:
        self.n = TextNormalizer()

    def test_double_quotes(self) -> None:
        assert self.n.normalize("\u201cHello\u201d") == '"Hello"'

    def test_single_quotes(self) -> None:
        assert self.n.normalize("\u2018Hello\u2019") == "'Hello'"


class TestEntityExpansion:
    """HTML entities should be decoded."""

    def setup_method(self) -> None:
        self.n = TextNormalizer()

    def test_ampersand(self) -> None:
        assert self.n.normalize("cats &amp; dogs") == "cats and dogs"

    def test_lt_gt(self) -> None:
        assert "less than" in self.n.normalize("&lt;")
        assert "greater than" in self.n.normalize("&gt;")

    def test_numeric_entities(self) -> None:
        result = self.n.normalize("&#8212; hello")
        assert "hello" in result


class TestWhitespace:
    """Excess whitespace should be collapsed."""

    def setup_method(self) -> None:
        self.n = TextNormalizer()

    def test_multiple_spaces(self) -> None:
        assert self.n.normalize("hello     world") == "hello world"

    def test_tabs(self) -> None:
        assert self.n.normalize("hello\t\tworld") == "hello world"


class TestEdgeCases:
    """Edge cases should behave reasonably."""

    def setup_method(self) -> None:
        self.n = TextNormalizer()

    def test_empty_string(self) -> None:
        assert self.n.normalize("") == ""

    def test_only_whitespace(self) -> None:
        assert self.n.normalize("   \t  \n  ") == ""

    def test_no_changes_needed(self) -> None:
        text = "This is ordinary text with no special characters."
        assert self.n.normalize(text) == text
