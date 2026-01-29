"""Tests for keyword matching logic."""


from hey_cleber.keywords import check_keyword

KEYWORDS = ("cleber", "kleber", "clever", "cleaver", "clebert")


class TestCheckKeyword:
    """Tests for check_keyword function."""

    def test_exact_match(self):
        assert check_keyword("cleber", KEYWORDS) is True

    def test_case_insensitive(self):
        assert check_keyword("CLEBER", KEYWORDS) is True
        assert check_keyword("Cleber", KEYWORDS) is True

    def test_keyword_in_sentence(self):
        assert check_keyword("hey cleber how are you", KEYWORDS) is True

    def test_phonetic_variant(self):
        assert check_keyword("I heard kleber say something", KEYWORDS) is True

    def test_clever_variant(self):
        assert check_keyword("that was clever", KEYWORDS) is True

    def test_no_match(self):
        assert check_keyword("hello world", KEYWORDS) is False

    def test_empty_text(self):
        assert check_keyword("", KEYWORDS) is False

    def test_whitespace_only(self):
        assert check_keyword("   ", KEYWORDS) is False

    def test_empty_keywords(self):
        assert check_keyword("cleber", ()) is False

    def test_partial_match_within_word(self):
        # "cleber" appears inside "clebert" keyword, but we test text containing keyword
        assert check_keyword("clebert is here", KEYWORDS) is True

    def test_keyword_with_punctuation(self):
        assert check_keyword("cleber!", KEYWORDS) is True
        assert check_keyword("hey, cleber.", KEYWORDS) is True

    def test_list_keywords(self):
        assert check_keyword("cleber", ["cleber", "kleber"]) is True

    def test_custom_keywords(self):
        assert check_keyword("jarvis activate", ("jarvis",)) is True
        assert check_keyword("hey siri", ("jarvis",)) is False
