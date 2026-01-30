"""Simple string-matching keyword detector."""

from __future__ import annotations

import logging

from hey_clever.config.settings import KeywordConfig
from hey_clever.ports.keyword_detection import IKeywordDetector

log = logging.getLogger(__name__)


class KeywordAdapter(IKeywordDetector):
    def __init__(self, config: KeywordConfig) -> None:
        self._keywords = config.keywords

    def detect(self, text: str) -> tuple[bool, float]:
        text_lower = text.lower().strip()
        if not text_lower:
            return False, 0.0
        for kw in self._keywords:
            if kw.lower() in text_lower:
                log.debug("Keyword match: '%s' in '%s'", kw, text_lower)
                return True, 1.0
        return False, 0.0

    def get_keywords(self) -> tuple[str, ...]:
        return self._keywords
