"""Extract structured text content from ebook formats."""

from __future__ import annotations

import re
from pathlib import Path

from opennarrator.exceptions import ExtractionError
from opennarrator.types import BookMetadata, Chapter

# ── Helpers ──────────────────────────────────────────────────────────────

_MIN_CHAPTER_CHARS = 200
"""Minimum text length for a valid chapter (shorter entries are filtered out)."""


def _strip_html(html: str) -> str:
    """Remove HTML tags and decode common entities, returning plain text."""
    text = html
    # Block-level tags → newline
    for tag in ("p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
        text = re.sub(rf"</?{tag}[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&mdash;", "\u2014")
    text = text.replace("&ndash;", "\u2013")
    text = text.replace("&nbsp;", " ")
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _strip_href_fragment(href: str) -> str:
    """Remove anchor fragment from an href (``file.html#anchor`` → ``file.html``)."""
    return href.split("#")[0] if "#" in href else href


# ── EPUB Extractor ───────────────────────────────────────────────────────


class EpubExtractor:
    """Extract chapters and metadata from EPUB files using ebooklib."""

    # TOC entry titles that indicate non-chapter content we should skip.
    _SKIP_PREFIXES = (
        "there are several editions",
        "contents",
        "characters",
        "preface",
        "introduction",
        "cover",
        "title page",
        "copyright",
        "colophon",
        "about the author",
        "also by",
        "the full project gutenberg",
        "end of the project gutenberg",
        "project gutenberg’s",
        "this ebook is for the use",
        "transcriber’s note",
        "table of contents",
    )

    # Titles to keep even though they look like metadata (real book titles).
    _KEEP_TITLES = (
        "a christmas carol",
        "the adventures of",
    )

    def extract(self, path: Path) -> BookMetadata:
        """Parse an EPUB file and return structured book data.

        Args:
            path: Path to the .epub file.

        Returns:
            BookMetadata containing chapters and metadata.

        Raises:
            ExtractionError: If the file is missing, malformed, or unreadable.
        """
        from ebooklib import epub

        if not path.exists():
            raise ExtractionError(f"File not found: {path}")
        if path.suffix.lower() != ".epub":
            raise ExtractionError(f"Expected .epub file, got {path.suffix}")

        try:
            book = epub.read_epub(str(path))
        except Exception as exc:
            raise ExtractionError(f"Failed to read EPUB {path}: {exc}") from exc

        # ── Metadata ──────────────────────────────────────────────────
        title = self._get_metadata(book, "DC", "title", path.stem)
        author = self._get_metadata(book, "DC", "creator", "Unknown Author")

        # ── Cover ─────────────────────────────────────────────────────
        cover_path: Path | None = None
        cover_item = self._find_cover(book)
        if cover_item is not None:
            cover_dir = path.parent / ".opennarrator_cache"
            cover_dir.mkdir(parents=True, exist_ok=True)
            cover_path = cover_dir / f"{path.stem}_cover.jpg"
            cover_path.write_bytes(cover_item.get_content())

        # ── Build href→item map ───────────────────────────────────────
        href_map: dict[str, object] = {}
        for item in book.get_items():
            if hasattr(item, "get_name"):
                name: str = item.get_name() or ""
                href_map[name] = item

        # ── Chapters via TOC ──────────────────────────────────────────
        chapters: list[Chapter] = []
        seen_hrefs: set[str] = set()

        for toc_item in self._walk_toc(book.toc):
            href: str | None = getattr(toc_item, "href", None)
            title_text: str | None = getattr(toc_item, "title", None)
            if not href or not title_text:
                continue

            # Skip non-chapter entries
            if title_text.lower().startswith(self._SKIP_PREFIXES):
                continue

            content = self._get_content_for_href(href_map, href)
            if not content:
                continue

            # Deduplicate: if the same href was used before, skip
            file_href = _strip_href_fragment(href)
            if file_href in seen_hrefs:
                continue
            seen_hrefs.add(file_href)

            # If the text starts with Gutenberg boilerplate, strip it off
            cleaned = self._strip_gutenberg_header(content)

            chapter = Chapter(
                index=len(chapters) + 1,
                title=title_text.strip(),
                text=cleaned,
            )
            chapters.append(chapter)

        # ── Fallback: spine order ─────────────────────────────────────
        if not chapters:
            chapters = self._spine_fallback(book)

        if not chapters:
            raise ExtractionError(f"No chapters found in {path}")

        return BookMetadata(
            title=title,
            author=author,
            cover_path=cover_path,
            chapters=chapters,
        )

    # ── Private helpers ────────────────────────────────────────────────

    @staticmethod
    def _strip_gutenberg_header(text: str) -> str:
        """Remove Project Gutenberg boilerplate from the start of text."""
        lines = text.split("\n")
        start_marker_idx = -1
        end_marker_idx = -1

        for i, line in enumerate(lines):
            upper = line.upper().strip()
            if "*** START OF" in upper and "PROJECT GUTENBERG" in upper:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                start_marker_idx = j
            if "*** END OF" in upper and "PROJECT GUTENBERG" in upper:
                end_marker_idx = i
                break

        if end_marker_idx >= 0:
            lines = lines[:end_marker_idx]
        if start_marker_idx > 0:
            lines = lines[start_marker_idx:]
        elif start_marker_idx < 0 and end_marker_idx < 0:
            while lines and (
                "project gutenberg" in lines[0].lower()
                or "this ebook" in lines[0].lower()
                or "several editions" in lines[0].lower()
                or lines[0].strip().startswith("***")
            ):
                lines.pop(0)
            while lines and not lines[0].strip():
                lines.pop(0)

        return "\n".join(lines).strip()

    @staticmethod
    def _get_metadata(book: object, namespace: str, name: str, fallback: str) -> str:
        """Get a single metadata value from the EPUB book."""
        try:
            values = book.get_metadata(namespace, name)
            if values and values[0]:
                return str(values[0][0])
        except Exception:
            pass
        return fallback

    @staticmethod
    def _find_cover(book: object) -> object | None:
        """Try to find the cover image in the EPUB."""
        from ebooklib import epub

        try:
            for item in book.get_items():
                if hasattr(item, "get_type") and item.get_type() == epub.ITEM_COVER:
                    return item
        except Exception:
            pass
        # Fallback: look for "cover" in IDs or names
        for candidate in ("cover", "coverpage", "cover-image"):
            try:
                item = book.get_item_with_id(candidate)
                if item is not None:
                    return item
            except Exception:
                pass
        return None

    @staticmethod
    def _walk_toc(toc: list) -> list:
        """Walk a possibly-nested EPUB TOC and yield every link/tuple item.

        Handles both flat ``[Link, Link, ...]`` and nested
        ``[(Section, [Link, ...]), ...]`` structures.
        """
        flat: list = []

        def _walk(entries):
            for entry in entries:
                if isinstance(entry, (list, tuple)):
                    for sub in entry:
                        if hasattr(sub, "href"):
                            flat.append(sub)
                        elif isinstance(sub, (list, tuple)):
                            _walk(sub)
                elif hasattr(entry, "href"):
                    flat.append(entry)
                if hasattr(entry, "items"):
                    items = list(entry.items) if callable(entry.items) else entry.items
                    _walk(items)

        _walk(toc)
        return flat

    @staticmethod
    def _get_content_for_href(href_map: dict[str, object], href: str) -> str:
        """Extract cleaned text from the item referenced by *href*.

        Strips anchor fragments and tries common prefixes (``text/``) to
        resolve items.
        """
        file_href = _strip_href_fragment(href)

        # Direct lookup
        item = href_map.get(file_href)
        if item is None:
            # Try ``text/`` prefix (ebooklib convention for some EPUBs)
            item = href_map.get(f"text/{file_href}")
        if item is None:
            # Try stripping any leading path components
            basename = file_href.rsplit("/", 1)[-1] if "/" in file_href else None
            if basename:
                for key, val in href_map.items():
                    if key.endswith(basename):
                        item = val
                        break

        if item is None or not hasattr(item, "get_body_content"):
            return ""

        try:
            raw = item.get_body_content()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            text = _strip_html(raw)
            if len(text) < _MIN_CHAPTER_CHARS:
                return ""
            return text
        except Exception:
            return ""

    @staticmethod
    def _spine_fallback(book: object) -> list[Chapter]:
        """Fallback when no TOC is available — use spine order."""
        from ebooklib import epub

        chapters: list[Chapter] = []
        try:
            for spine_id, _ in book.spine:
                item = book.get_item_with_id(spine_id)
                if item is None or not hasattr(item, "get_type"):
                    continue
                if item.get_type() != epub.ITEM_DOCUMENT:
                    continue
                raw = item.get_body_content()
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="replace")
                text = _strip_html(raw)
                if len(text) >= _MIN_CHAPTER_CHARS:
                    chapters.append(
                        Chapter(
                            index=len(chapters) + 1,
                            title=f"Chapter {len(chapters) + 1}",
                            text=text,
                        )
                    )
        except Exception:
            pass
        return chapters


# ── TXT Extractor ────────────────────────────────────────────────────────────


class TxtExtractor:
    """Extract chapters from plain text files using regex chapter detection.

    Supports common chapter heading formats:
    - ``Chapter 1``, ``Chapter 2``, ...
    - ``CHAPTER I``, ``CHAPTER II``, ... (roman numerals)
    - ``CHAPTER ONE``, ``CHAPTER TWO``, ...
    - ``Stave One``, ``Stave Two``, ...
    - ``1.``, ``2.``, ... (numbered sections at line start)
    """

    # Pattern order matters: more specific patterns first.
    _CHAPTER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        # "Chapter 1" or "CHAPTER 1" (Arabic numerals)
        (
            re.compile(
                r"^(?:Chapter|CHAPTER|Stave|STAVE|Part|PART)\s+(\d+|[A-Z]+)\s*[:.\-]?\s*(.*)$",
                re.MULTILINE,
            ),
            "{prefix} {number}",
        ),  # noqa: E501
        # "CHAPTER ONE" or "CHAPTER TWO" (word numerals)
        (
            re.compile(
                r"^(?:CHAPTER|Chapter)\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)\s*[:.\-]?\s*(.*)$",
                re.MULTILINE,
            ),
            "{prefix} {number}",
        ),  # noqa: E501
    ]

    def extract(self, path: Path) -> BookMetadata:
        """Parse a plain text file and return structured book data.

        Args:
            path: Path to the .txt file.

        Returns:
            BookMetadata containing detected chapters.

        Raises:
            ExtractionError: If the file is missing, empty, or unreadable.
        """
        if not path.exists():
            raise ExtractionError(f"File not found: {path}")

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ExtractionError(f"Failed to read {path}: {exc}") from exc

        chapters = self._detect_chapters(text)

        if not chapters:
            # Fallback: treat whole file as one chapter
            cleaned = text.strip()
            if cleaned:
                chapters = [Chapter(index=1, title="Chapter 1", text=cleaned)]

        if not chapters:
            raise ExtractionError(f"No chapters found in {path}")

        return BookMetadata(
            title=path.stem,
            author="Unknown Author",
            chapters=chapters,
        )

    def _detect_chapters(self, text: str) -> list[Chapter]:
        """Split text into chapters by detecting headings.

        Splits on the first matching chapter heading pattern, then
        groups remaining content into chapter bodies.
        """
        lines = text.split("\n")
        chapter_boundaries: list[tuple[int, str]] = []  # (line_index, title)

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            for pattern, _ in self._CHAPTER_PATTERNS:
                m = pattern.match(line + "\n")
                if m:
                    # Reconstruct a good title
                    raw = stripped
                    chapter_boundaries.append((i, raw))
                    break

        if not chapter_boundaries:
            return []

        chapters: list[Chapter] = []
        for idx, (start_idx, title) in enumerate(chapter_boundaries):
            # Determine end line
            if idx + 1 < len(chapter_boundaries):
                end_idx = chapter_boundaries[idx + 1][0]
            else:
                end_idx = len(lines)

            content_lines = lines[start_idx + 1 : end_idx]
            text = "\n".join(line for line in content_lines if line.strip()).strip()
            if text:
                chapters.append(Chapter(index=len(chapters) + 1, title=title, text=text))

        return chapters
