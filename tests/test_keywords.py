"""Tests for keyword adapter."""

from hey_clever.adapters.keyword_adapter import KeywordAdapter
from hey_clever.config.settings import KeywordConfig

KEYWORDS = ("clever", "klever", "cleber", "kleber", "cleaver")


def _make_adapter(keywords: tuple[str, ...] = KEYWORDS) -> KeywordAdapter:
    return KeywordAdapter(KeywordConfig(keywords=keywords))


class TestKeywordAdapter:
    def test_exact_match(self):
        detected, conf = _make_adapter().detect("clever")
        assert detected is True
        assert conf == 1.0

    def test_case_insensitive(self):
        assert _make_adapter().detect("CLEVER")[0] is True
        assert _make_adapter().detect("Clever")[0] is True

    def test_keyword_in_sentence(self):
        assert _make_adapter().detect("hey clever how are you")[0] is True

    def test_phonetic_variant(self):
        assert _make_adapter().detect("I heard kleber say something")[0] is True

    def test_no_match(self):
        detected, conf = _make_adapter().detect("hello world")
        assert detected is False
        assert conf == 0.0

    def test_empty_text(self):
        assert _make_adapter().detect("")[0] is False

    def test_whitespace_only(self):
        assert _make_adapter().detect("   ")[0] is False

    def test_empty_keywords(self):
        assert _make_adapter(keywords=()).detect("clever")[0] is False

    def test_with_punctuation(self):
        assert _make_adapter().detect("clever!")[0] is True
        assert _make_adapter().detect("hey, clever.")[0] is True

    def test_get_keywords(self):
        adapter = _make_adapter()
        assert adapter.get_keywords() == KEYWORDS

    def test_custom_keywords(self):
        adapter = _make_adapter(keywords=("jarvis",))
        assert adapter.detect("jarvis activate")[0] is True
        assert adapter.detect("hey siri")[0] is False
