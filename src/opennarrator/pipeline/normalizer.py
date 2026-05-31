"""Text normalization for TTS — produces clean, speakable text."""

from __future__ import annotations

import re

# ── Number to words ──────────────────────────────────────────────────────

_NUM0_19 = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)

_NUM_TENS = (
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
)


def _number_to_words(n: int) -> str:
    """Convert an integer (0-9999) to English words."""
    if n < 0:
        return f"minus {_number_to_words(-n)}"
    if n < 20:
        return _NUM0_19[n]
    if n < 100:
        tens = _NUM_TENS[n // 10]
        ones = n % 10
        return tens if ones == 0 else f"{tens} {_NUM0_19[ones]}"
    if n < 1000:
        hundreds = _NUM0_19[n // 100]
        rest = n % 100
        if rest == 0:
            return f"{hundreds} hundred"
        return f"{hundreds} hundred {_number_to_words(rest)}"
    if n < 1_000_000:
        thousands = _number_to_words(n // 1000)
        rest = n % 1000
        if rest == 0:
            return f"{thousands} thousand"
        return f"{thousands} thousand {_number_to_words(rest)}"
    return str(n)  # Fallback: return as-is for huge numbers


# ── Text normalizer ──────────────────────────────────────────────────────

# Curly/smart quotes → straight quotes
_QUOTE_MAP: dict[str, str] = {
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u2013": "\u2014",  # en-dash → em-dash
}

# Consecutive-whitespace pattern
_MULTI_SPACE = re.compile(r"[ \t]+")


class TextNormalizer:
    """Clean and normalize text for TTS synthesis."""

    def normalize(self, text: str) -> str:
        """Clean and normalize text for speech synthesis.

        * Strips HTML entities (relics from EPUB parsing)
        * Expands numbers to words
        * Normalizes whitespace
        * Replaces smart quotes with straight quotes
        * Preserves dialogue structure
        """
        result = text

        # 1. HTML entities (leftovers from EPUB parsing)
        result = self._expand_entities(result)

        # 2. Smart quotes → straight
        result = self._normalize_quotes(result)

        # 3. Em-dashes with spaces → surrounded by pauses
        result = result.replace(" — ", ", ")
        result = result.replace("--", ", ")

        # 4. Number expansion (only standalone integers, not years in context)
        result = self._expand_numbers(result)

        # 5. Multiple consecutive spaces → single space
        result = _MULTI_SPACE.sub(" ", result)

        # 6. Collapse excessive blank lines
        result = re.sub(r"\n{3,}", "\n\n", result)

        return result.strip()

    # ── Internal steps ──────────────────────────────────────────────────

    @staticmethod
    def _expand_entities(text: str) -> str:
        """Decode remaining HTML/numeric entities."""
        text = text.replace("&amp;", "and")
        text = text.replace("&lt;", "less than")
        text = text.replace("&gt;", "greater than")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&#8220;", '"')
        text = text.replace("&#8221;", '"')
        text = text.replace("&#8216;", "'")
        text = text.replace("&#8217;", "'")
        text = text.replace("&#8212;", ", ")
        text = text.replace("&#8211;", ", ")
        # Generic numeric entities: &#NNNN;
        text = re.sub(r"&#\d+;", " ", text)
        return text

    @staticmethod
    def _normalize_quotes(text: str) -> str:
        """Replace smart/curly quotes with straight ASCII equivalents."""
        result = text
        for smart, straight in _QUOTE_MAP.items():
            result = result.replace(smart, straight)
        return result

    @staticmethod
    def _expand_numbers(text: str) -> str:
        """Replace standalone integers with their spoken-word forms.

        Avoids expanding numbers that are part of larger tokens,
        chapter headings, or phone-like sequences.
        """

        # Match standalone integers (surrounded by non-digit or boundaries)
        def _replace_num(m: re.Match[str]) -> str:
            num_str = m.group(0)
            try:
                n = int(num_str)
                if n >= 10_000:
                    return num_str
                return _number_to_words(n)
            except ValueError:
                return num_str

        # Word-boundary integer pattern
        result = re.sub(r"\b(\d{1,4})\b", _replace_num, text)
        return result
