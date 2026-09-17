"""Candidate model and keyword scoring (domain, standard library only).

A HumanTurn is format-neutral: the transcript adapter builds it, the domain never sees
JSON. Scores follow docs/requirements/extraction.md FR-106 / FR-107; the numbers live
here once and the tests take their expected values from the requirements document.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

TAG = "#表現"
TAG_SCORE = 10
STRONG_KEYWORDS: tuple[str, ...] = (
    "わかりづらい",
    "分かりづらい",
    "不自然",
    "言い回し",
    "表現",
    "AIっぽい",
    "揺れ",
)
STRONG_SCORE = 3
WEAK_KEYWORDS: tuple[str, ...] = ("ではなく", "直して", "言い換え")
WEAK_SCORE = 1
# Weak keywords are mostly ordinary instructions in long turns (2026-09-18 survey).
WEAK_MAX_CHARS = 200

_JAPANESE = re.compile(r"[ぁ-んァ-ン一-龥]")


@dataclass(frozen=True)
class HumanTurn:
    """One human utterance with the context needed for triage."""

    text: str
    timestamp: str | None  # ISO 8601 as recorded, or None when the record has none
    session_id: str
    project: str
    preceding_assistant: str  # "" when no assistant text preceded the turn in the session


@dataclass(frozen=True)
class Candidate:
    turn: HumanTurn
    score: int
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class ScanStats:
    files_scanned: int
    human_turns: int
    skipped_lines: int


def contains_japanese(text: str) -> bool:
    return _JAPANESE.search(text) is not None


def score_turn(turn: HumanTurn) -> Candidate | None:
    """Score one turn; None when it is not a candidate (no Japanese or score 0)."""
    if not contains_japanese(turn.text):
        return None
    score = 0
    keywords: list[str] = []
    if TAG in turn.text:
        score += TAG_SCORE
        keywords.append(TAG)
    for keyword in STRONG_KEYWORDS:
        if keyword in turn.text:
            score += STRONG_SCORE
            keywords.append(keyword)
    if len(turn.text) <= WEAK_MAX_CHARS:
        for keyword in WEAK_KEYWORDS:
            if keyword in turn.text:
                score += WEAK_SCORE
                keywords.append(keyword)
    if score == 0:
        return None
    return Candidate(turn, score, tuple(keywords))


def rank(candidates: Iterable[Candidate]) -> tuple[Candidate, ...]:
    """Score descending, then timestamp descending; undated candidates last (FR-107)."""
    by_time = sorted(candidates, key=lambda c: c.turn.timestamp or "", reverse=True)
    return tuple(sorted(by_time, key=lambda c: -c.score))
