"""Builders for extraction tests: a HumanTurn with sensible defaults, overridable per test."""

from __future__ import annotations

from src.modules.extraction.domain.candidate import HumanTurn


def turn(
    text: str = "この言い回しがわかりづらい。",
    *,
    timestamp: str | None = "2026-09-17T10:00:00.000Z",
    session_id: str = "session-a",
    project: str = "-Users-me-Project-demo",
    preceding_assistant: str = "修正しました。どうですか。",
) -> HumanTurn:
    return HumanTurn(
        text=text,
        timestamp=timestamp,
        session_id=session_id,
        project=project,
        preceding_assistant=preceding_assistant,
    )
