"""Unit tests for candidate scoring and ranking (domain).

Expected scores are computed by hand from docs/requirements/extraction.md FR-106 / FR-107
(`#表現` 10, each strong keyword kind 3, each weak keyword kind 1 only when the turn is
200 characters or shorter, score 0 → not a candidate), never from the implementation.
"""

from __future__ import annotations

import unittest

from src.modules.extraction.domain.candidate import (
    STRONG_KEYWORDS,
    WEAK_KEYWORDS,
    rank,
    score_turn,
)

from .builders import turn


class TestKeywordVocabulary(unittest.TestCase):
    def test_vocabulary_matches_the_requirements_document(self) -> None:
        # Literals from docs/requirements/extraction.md FR-106.
        self.assertEqual(
            ("わかりづらい", "分かりづらい", "不自然", "言い回し", "表現", "AIっぽい", "揺れ"),
            STRONG_KEYWORDS,
        )
        self.assertEqual(("ではなく", "直して", "言い換え"), WEAK_KEYWORDS)


class TestScore(unittest.TestCase):
    def test_one_strong_keyword_scores_3(self) -> None:
        candidate = score_turn(turn("ここが不自然です。"))
        assert candidate is not None
        self.assertEqual(3, candidate.score)
        self.assertEqual(("不自然",), candidate.keywords)

    def test_two_different_strong_keywords_score_6(self) -> None:
        candidate = score_turn(turn("言い回しが不自然。"))
        assert candidate is not None
        self.assertEqual(6, candidate.score)

    def test_the_same_strong_keyword_twice_counts_once(self) -> None:
        candidate = score_turn(turn("不自然。ここも不自然。"))
        assert candidate is not None
        self.assertEqual(3, candidate.score)

    def test_tag_scores_10_plus_the_strong_keyword_it_contains(self) -> None:
        # 「#表現」 carries the tag (10) and contains the strong keyword 「表現」 (3).
        candidate = score_turn(turn("#表現 ここの語尾。"))
        assert candidate is not None
        self.assertEqual(13, candidate.score)
        self.assertIn("#表現", candidate.keywords)

    def test_weak_keyword_in_a_short_turn_scores_1(self) -> None:
        candidate = score_turn(turn("「実施」ではなく「行う」で。"))
        assert candidate is not None
        self.assertEqual(1, candidate.score)
        self.assertEqual(("ではなく",), candidate.keywords)

    def test_weak_keyword_in_a_turn_longer_than_200_characters_does_not_score(self) -> None:
        long_text = "ではなく" + "あ" * 197  # 201 characters
        self.assertIsNone(score_turn(turn(long_text)))

    def test_weak_keyword_at_exactly_200_characters_scores(self) -> None:
        text = "ではなく" + "あ" * 196  # 200 characters
        candidate = score_turn(turn(text))
        assert candidate is not None
        self.assertEqual(1, candidate.score)

    def test_strong_keyword_still_scores_in_a_long_turn_while_weak_does_not(self) -> None:
        text = "ではなく、この表現は" + "あ" * 200
        candidate = score_turn(turn(text))
        assert candidate is not None
        self.assertEqual(3, candidate.score)
        self.assertEqual(("表現",), candidate.keywords)

    def test_turn_without_keywords_is_not_a_candidate(self) -> None:
        self.assertIsNone(score_turn(turn("表を 3 列にしてください。")))

    def test_turn_without_japanese_is_not_a_candidate(self) -> None:
        self.assertIsNone(score_turn(turn("Please rewrite this; it is unnatural.")))

    def test_candidate_keeps_the_turn(self) -> None:
        source = turn("不自然。")
        candidate = score_turn(source)
        assert candidate is not None
        self.assertIs(source, candidate.turn)


class TestRank(unittest.TestCase):
    def test_orders_by_score_descending_then_timestamp_descending(self) -> None:
        low_new = score_turn(turn("ではなく。", timestamp="2026-09-18T00:00:00Z"))
        high_old = score_turn(turn("不自然。", timestamp="2026-09-01T00:00:00Z"))
        high_new = score_turn(turn("不自然。", timestamp="2026-09-17T00:00:00Z"))
        assert low_new and high_old and high_new
        ranked = rank([low_new, high_old, high_new])
        self.assertEqual(
            [(3, "2026-09-17T00:00:00Z"), (3, "2026-09-01T00:00:00Z"), (1, "2026-09-18T00:00:00Z")],
            [(c.score, c.turn.timestamp) for c in ranked],
        )

    def test_candidates_without_timestamp_sort_after_dated_ones_of_equal_score(self) -> None:
        undated = score_turn(turn("不自然。", timestamp=None))
        dated = score_turn(turn("不自然。", timestamp="2026-01-01T00:00:00Z"))
        assert undated and dated
        self.assertEqual([dated, undated], list(rank([undated, dated])))


if __name__ == "__main__":
    unittest.main()
