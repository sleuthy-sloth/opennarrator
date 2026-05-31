"""Custom exception hierarchy for OpenNarrator."""


class OpenNarratorError(Exception):
    """Base exception for all OpenNarrator errors."""


class ExtractionError(OpenNarratorError):
    """Raised when text extraction from an ebook fails."""


class SynthesisError(OpenNarratorError):
    """Raised when TTS synthesis fails."""


class PackagingError(OpenNarratorError):
    """Raised during M4B assembly."""
