"""Unit tests for the Markdown candidate report (domain, pure rendering).

The layout requirements come from docs/requirements/extraction.md FR-110: header fields,
per-candidate fields, 400/200-character excerpts, 「不明」 for a missing date.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

from src.modules.extraction.domain.candidate import ScanStats, score_turn
from src.modules.extraction.domain.report import render_report

from .builders import turn

STATS = ScanStats(files_scanned=3, human_turns=40, skipped_lines=2)
HEADER = {
    "generated_at": "2026-09-18T09:00:00",
    "projects_dir": "/Users/me/.claude/projects",
    "since": "2026-06-01",
    "min_score": 1,
}


def candidate(text: str = "この言い回しがわかりづらい。", **turn_overrides):
    result = score_turn(turn(text, **turn_overrides))
    assert result is not None
    return result


class TestDuplicateSessions(unittest.TestCase):
    def test_sessions_that_replayed_the_turn_are_listed_beside_the_session(self) -> None:
        merged = replace(candidate(), duplicate_sessions=("session-b", "session-c"))
        report = render_report([merged], STATS, **HEADER)
        self.assertIn("`session-a`（同一発話: `session-b`, `session-c`）", report)

    def test_a_candidate_without_duplicates_shows_the_session_alone(self) -> None:
        report = render_report([candidate()], STATS, **HEADER)
        self.assertIn("- セッション: `session-a`\n", report)
        self.assertNotIn("同一発話", report)


class TestHeader(unittest.TestCase):
    def test_header_lists_generation_parameters_and_scan_statistics(self) -> None:
        report = render_report([candidate()], STATS, **HEADER)
        for expected in (
            "2026-09-18T09:00:00",
            "/Users/me/.claude/projects",
            "2026-06-01",
            "走査ファイル数 | 3",
            "人間の発話数 | 40",
            "読み飛ばし行数 | 2",
            "候補数 | 1",
        ):
            self.assertIn(expected, report)

    def test_header_shows_no_period_when_since_is_absent(self) -> None:
        report = render_report([], STATS, **{**HEADER, "since": None})
        self.assertIn("期間 | 全期間", report)
        self.assertIn("候補数 | 0", report)


class TestCandidateSection(unittest.TestCase):
    def test_candidate_fields_are_present(self) -> None:
        report = render_report([candidate()], STATS, **HEADER)
        self.assertIn("## 1. スコア 6 — 2026-09-17 — -Users-me-Project-demo", report)
        self.assertIn("セッション: `session-a`", report)
        self.assertIn("キーワード: わかりづらい, 言い回し", report)
        self.assertIn("> この言い回しがわかりづらい。", report)
        self.assertIn("> 修正しました。どうですか。", report)

    def test_missing_timestamp_is_shown_as_unknown(self) -> None:
        report = render_report([candidate(timestamp=None)], STATS, **HEADER)
        self.assertIn("スコア 6 — 不明 —", report)

    def test_empty_preceding_assistant_text_is_marked(self) -> None:
        report = render_report([candidate(preceding_assistant="")], STATS, **HEADER)
        self.assertIn("（直前の assistant 本文なし）", report)

    def test_turn_text_is_cut_at_400_characters_with_an_ellipsis(self) -> None:
        report = render_report([candidate("不自然" + "あ" * 500)], STATS, **HEADER)
        self.assertIn("不自然" + "あ" * 397 + "…", report)
        self.assertNotIn("あ" * 398, report)

    def test_assistant_text_is_cut_at_200_characters_with_an_ellipsis(self) -> None:
        report = render_report([candidate(preceding_assistant="い" * 250)], STATS, **HEADER)
        self.assertIn("い" * 200 + "…", report)
        self.assertNotIn("い" * 201, report)

    def test_multiline_excerpts_are_quoted_on_every_line(self) -> None:
        report = render_report([candidate("不自然です。\n二行目。")], STATS, **HEADER)
        self.assertIn("> 不自然です。\n> 二行目。", report)

    def test_rendering_is_deterministic(self) -> None:
        candidates = [candidate(), candidate("#表現 語尾。", session_id="session-b")]
        self.assertEqual(
            render_report(candidates, STATS, **HEADER), render_report(candidates, STATS, **HEADER)
        )


if __name__ == "__main__":
    unittest.main()
