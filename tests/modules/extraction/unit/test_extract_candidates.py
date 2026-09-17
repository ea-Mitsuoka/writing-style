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


if __name__ == "__main__":
    unittest.main()
