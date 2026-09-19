"""Extraction application — the ExtractCandidates use case.

Scans turns through the TranscriptSource port, scores them with the domain, drops
non-candidates and those under `min_score`, and returns them ranked with the scan
statistics. Rendering and writing belong to the domain report and the interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..domain.candidate import Candidate, ScanStats, deduplicate, rank, score_turn
from .ports import TranscriptSource


@dataclass(frozen=True)
class Extraction:
    candidates: tuple[Candidate, ...]
    stats: ScanStats


class ExtractCandidates:
    def __init__(self, source: TranscriptSource) -> None:
        self._source = source

    def handle(self, since: date | None, min_score: int) -> Extraction:
        result = self._source.scan(since)
        scored = (score_turn(turn) for turn in result.turns)
        kept = [c for c in scored if c is not None and c.score >= min_score]
        return Extraction(rank(deduplicate(kept)), result.stats)
