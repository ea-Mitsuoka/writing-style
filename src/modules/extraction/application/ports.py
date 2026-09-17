"""Extraction application ports.

A TranscriptSource turns whatever the recording format is into format-neutral HumanTurns
plus scan statistics (ARC-002: the adapter lives in `infrastructure/`). `since` is the
first day to include; None means everything.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from ..domain.candidate import HumanTurn, ScanStats


@dataclass(frozen=True)
class ScanResult:
    turns: tuple[HumanTurn, ...]
    stats: ScanStats


class TranscriptSource(Protocol):
    def scan(self, since: date | None) -> ScanResult: ...
