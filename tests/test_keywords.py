"""Tests for keyword matching logic."""

from hey_clever.keywords import check_keyword

KEYWORDS = ("clever", "klever", "cleber", "kleber", "cleaver")


class TestCheckKeyword:
    """Tests for check_keyword function."""

    def test_exact_match(self):
        assert check_keyword("clever", KEYWORDS) is True

    def test_case_insensitive(self):
        assert check_keyword("CLEVER", KEYWORDS) is True
        assert check_keyword("Clever", KEYWORDS) is True

    def test_keyword_in_sentence(self):
        assert check_keyword("hey clever how are you", KEYWORDS) is True

    def test_phonetic_variant(self):
        assert check_keyword("I heard kleber say something", KEYWORDS) is True

    def test_cleber_variant(self):
        assert check_keyword("that was cleber", KEYWORDS) is True

    def test_no_match(self):
        assert check_keyword("hello world", KEYWORDS) is False

    def test_empty_text(self):
        assert check_keyword("", KEYWORDS) is False

    def test_whitespace_only(self):
        assert check_keyword("   ", KEYWORDS) is False

    def test_empty_keywords(self):
        assert check_keyword("clever", ()) is False

    def test_partial_match_within_word(self):
        assert check_keyword("cleaver is here", KEYWORDS) is True

    def test_keyword_with_punctuation(self):
        assert check_keyword("clever!", KEYWORDS) is True
        assert check_keyword("hey, clever.", KEYWORDS) is True

    def test_list_keywords(self):
        assert check_keyword("clever", ["clever", "klever"]) is True

    def test_custom_keywords(self):
        assert check_keyword("jarvis activate", ("jarvis",)) is True
        assert check_keyword("hey siri", ("jarvis",)) is False
