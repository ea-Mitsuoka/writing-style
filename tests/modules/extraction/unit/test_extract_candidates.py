"""Unit tests for the ExtractCandidates use case (application) with a fake TranscriptSource."""

from __future__ import annotations

import unittest
from datetime import date

from src.modules.extraction.application.extract_candidates import ExtractCandidates
from src.modules.extraction.application.ports import ScanResult
from src.modules.extraction.domain.candidate import ScanStats

from .builders import turn

STATS = ScanStats(files_scanned=2, human_turns=5, skipped_lines=0)


class FakeTranscriptSource:
    def __init__(self, turns) -> None:
        self._turns = tuple(turns)
        self.since_seen: list[date | None] = []

    def scan(self, since: date | None) -> ScanResult:
        self.since_seen.append(since)
        return ScanResult(turns=self._turns, stats=STATS)


class TestExtractCandidates(unittest.TestCase):
    def test_returns_ranked_candidates_and_passes_statistics_through(self) -> None:
        source = FakeTranscriptSource(
            [
                turn("表を 3 列にして。"),  # no keyword → dropped
                turn("ではなく。", timestamp="2026-09-18T00:00:00Z"),  # 1
                turn("不自然。", timestamp="2026-09-01T00:00:00Z"),  # 3
            ]
        )
        extraction = ExtractCandidates(source).handle(since=None, min_score=1)
        self.assertEqual([3, 1], [c.score for c in extraction.candidates])
        self.assertEqual(STATS, extraction.stats)

    def test_min_score_drops_lower_candidates(self) -> None:
        source = FakeTranscriptSource([turn("ではなく。"), turn("不自然。")])
        extraction = ExtractCandidates(source).handle(since=None, min_score=3)
        self.assertEqual([3], [c.score for c in extraction.candidates])

    def test_since_is_forwarded_to_the_source(self) -> None:
        source = FakeTranscriptSource([])
        ExtractCandidates(source).handle(since=date(2026, 6, 1), min_score=1)
        self.assertEqual([date(2026, 6, 1)], source.since_seen)

    def test_empty_scan_yields_no_candidates(self) -> None:
        extraction = ExtractCandidates(FakeTranscriptSource([])).handle(since=None, min_score=1)
        self.assertEqual((), extraction.candidates)


class TestDuplicateTurns(unittest.TestCase):
    """Resumed sessions and renamed project directories replay the same turn (#12)."""

    def test_same_text_and_timestamp_is_reported_once_with_the_other_sessions(self) -> None:
        source = FakeTranscriptSource(
            [
                turn("不自然。", session_id="session-a"),
                turn("不自然。", session_id="session-b"),
                turn("不自然。", session_id="session-c", project="-Users-me-Project-renamed"),
            ]
        )
        extraction = ExtractCandidates(source).handle(since=None, min_score=1)
        self.assertEqual(1, len(extraction.candidates))
        kept = extraction.candidates[0]
        self.assertEqual("session-a", kept.turn.session_id)
        self.assertEqual(("session-b", "session-c"), kept.duplicate_sessions)

    def test_a_repeated_session_id_is_listed_once(self) -> None:
        source = FakeTranscriptSource(
            [turn("不自然。", session_id="session-a"), turn("不自然。", session_id="session-b")] * 2
        )
        extraction = ExtractCandidates(source).handle(since=None, min_score=1)
        self.assertEqual(("session-b",), extraction.candidates[0].duplicate_sessions)

    def test_same_text_at_different_times_stays_separate(self) -> None:
        source = FakeTranscriptSource(
            [
                turn("不自然。", timestamp="2026-09-18T00:00:00Z"),
                turn("不自然。", timestamp="2026-09-17T00:00:00Z"),
            ]
        )
        extraction = ExtractCandidates(source).handle(since=None, min_score=1)
        self.assertEqual(2, len(extraction.candidates))
        self.assertEqual([(), ()], [c.duplicate_sessions for c in extraction.candidates])

    def test_different_text_at_the_same_time_stays_separate(self) -> None:
        source = FakeTranscriptSource([turn("不自然。"), turn("この言い回しは不自然。")])
        extraction = ExtractCandidates(source).handle(since=None, min_score=1)
        self.assertEqual(2, len(extraction.candidates))

    def test_undated_duplicates_are_merged(self) -> None:
        source = FakeTranscriptSource(
            [
                turn("不自然。", timestamp=None, session_id="session-a"),
                turn("不自然。", timestamp=None, session_id="session-b"),
            ]
        )
        extraction = ExtractCandidates(source).handle(since=None, min_score=1)
        self.assertEqual(1, len(extraction.candidates))
        self.assertEqual(("session-b",), extraction.candidates[0].duplicate_sessions)

    def test_a_turn_seen_once_records_no_duplicate_sessions(self) -> None:
        extraction = ExtractCandidates(FakeTranscriptSource([turn("不自然。")])).handle(
            since=None, min_score=1
        )
        self.assertEqual((), extraction.candidates[0].duplicate_sessions)


if __name__ == "__main__":
    unittest.main()
