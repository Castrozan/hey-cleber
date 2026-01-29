"""Keyword matching logic for wake word detection."""

from __future__ import annotations

import logging

log = logging.getLogger("hey-cleber.keywords")


def check_keyword(text: str, keywords: tuple[str, ...] | list[str]) -> bool:
    """Check if any keyword appears in the transcription (case-insensitive).

    Args:
        text: Transcribed text to search.
        keywords: Sequence of keywords to look for.

    Returns:
        True if any keyword is found in the text.
    """
    text_lower = text.lower().strip()
    if not text_lower:
        return False
    for kw in keywords:
        if kw.lower() in text_lower:
            log.debug("Keyword match: '%s' found in '%s'", kw, text_lower)
            return True
    return False
