"""Claude Code transcript adapter implementing the TranscriptSource port.

Walks `<projects-dir>/**/*.jsonl` in sorted order (FR-101), pairs each human turn with the
assistant text that preceded it in the same file (FR-104), applies `--since` on the
record timestamp (FR-108; undated records are kept), and counts unparseable lines instead
of stopping. It only reads (C-2).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ..application.ports import ScanResult
from ..domain.candidate import HumanTurn, ScanStats
from .claude_code_records import assistant_text, human_text, record_timestamp


class TranscriptsUnavailable(Exception):
    """The projects directory is missing or holds no `.jsonl` file (FR-112)."""


class ClaudeCodeTranscriptSource:
    def __init__(self, projects_dir: Path) -> None:
        self._dir = projects_dir

    def scan(self, since: date | None) -> ScanResult:
        if not self._dir.is_dir():
            raise TranscriptsUnavailable(f"{self._dir} is not a directory")
        files = sorted(path for path in self._dir.rglob("*.jsonl") if path.is_file())
        if not files:
            raise TranscriptsUnavailable(f"no .jsonl files under {self._dir}")

        turns: list[HumanTurn] = []
        human_turns = 0
        skipped = 0
        for path in files:
            project = path.relative_to(self._dir).parts[0]
            session_id = path.stem
            preceding = ""
            with path.open(encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    record = _decode(line)
                    if record is None:
                        skipped += 1
                        continue
                    assistant = assistant_text(record)
                    if assistant is not None:
                        preceding = assistant
                        continue
                    text = human_text(record)
                    if text is None:
                        continue
                    human_turns += 1
                    timestamp = record_timestamp(record)
                    if since is not None and not _on_or_after(timestamp, since):
                        continue
                    turns.append(HumanTurn(text, timestamp, session_id, project, preceding))
        return ScanResult(tuple(turns), ScanStats(len(files), human_turns, skipped))


def _decode(line: str) -> dict | None:
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None
    return record if isinstance(record, dict) else None


def _on_or_after(timestamp: str | None, since: date) -> bool:
    # A record without a usable date is kept: dropping it silently would lose recall.
    if timestamp is None:
        return True
    try:
        return date.fromisoformat(timestamp[:10]) >= since
    except ValueError:
        return True
