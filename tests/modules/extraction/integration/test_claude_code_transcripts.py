"""Integration tests for the Claude Code transcript source over real JSONL files in a temp dir.

Fixture records mirror the shapes seen in the 2026-09-18 survey (A-1); expectations are
FR-101 … FR-104 and FR-108.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.modules.extraction.infrastructure.claude_code_transcripts import (
    ClaudeCodeTranscriptSource,
    TranscriptsUnavailable,
)


def assistant(text: str, ts: str) -> dict:
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def human(text: str, ts: str, **flags) -> dict:
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}, **flags}


def tool_result(ts: str) -> dict:
    return {
        "type": "user",
        "timestamp": ts,
        "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]},
    }


class TranscriptCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.projects = Path(self._tmp.name) / "projects"
        self.projects.mkdir()

    def write_session(
        self, project: str, session: str, records: list, raw_lines: list[str] = ()
    ) -> None:
        directory = self.projects / project
        directory.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(r, ensure_ascii=False) for r in records] + list(raw_lines)
        (directory / f"{session}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestScan(TranscriptCase):
    def test_human_turns_are_paired_with_the_preceding_assistant_text(self) -> None:
        self.write_session(
            "-Users-me-Project-demo",
            "s1",
            [
                assistant("修正しました。", "2026-09-17T10:00:00Z"),
                human("この言い回しが不自然。", "2026-09-17T10:01:00Z"),
                tool_result("2026-09-17T10:02:00Z"),
                assistant("再修正しました。", "2026-09-17T10:03:00Z"),
                human("自動メッセージ", "2026-09-17T10:04:00Z", isMeta=True),
                human("まだ表現が硬い。", "2026-09-17T10:05:00Z"),
            ],
        )

        result = ClaudeCodeTranscriptSource(self.projects).scan(since=None)

        self.assertEqual(
            [
                ("この言い回しが不自然。", "修正しました。"),
                ("まだ表現が硬い。", "再修正しました。"),
            ],
            [(t.text, t.preceding_assistant) for t in result.turns],
        )
        self.assertEqual("-Users-me-Project-demo", result.turns[0].project)
        self.assertEqual("s1", result.turns[0].session_id)
        self.assertEqual("2026-09-17T10:01:00Z", result.turns[0].timestamp)
        self.assertEqual(1, result.stats.files_scanned)
        self.assertEqual(2, result.stats.human_turns)

    def test_first_human_turn_without_preceding_assistant_has_empty_context(self) -> None:
        self.write_session("p", "s1", [human("最初の発話。", "2026-09-17T10:00:00Z")])
        [turn] = ClaudeCodeTranscriptSource(self.projects).scan(since=None).turns
        self.assertEqual("", turn.preceding_assistant)

    def test_unparseable_lines_are_counted_and_skipped(self) -> None:
        self.write_session(
            "p", "s1", [human("不自然。", "2026-09-17T10:00:00Z")], raw_lines=["{not json", ""]
        )
        result = ClaudeCodeTranscriptSource(self.projects).scan(since=None)
        self.assertEqual(1, len(result.turns))
        self.assertEqual(1, result.stats.skipped_lines)

    def test_since_keeps_turns_on_or_after_the_date_and_undated_turns(self) -> None:
        self.write_session(
            "p",
            "s1",
            [
                human("古い。不自然。", "2026-05-31T23:59:59Z"),
                human("境界。不自然。", "2026-06-01T00:00:00Z"),
                {"type": "user", "message": {"role": "user", "content": "日時なし。不自然。"}},
            ],
        )
        result = ClaudeCodeTranscriptSource(self.projects).scan(since=date(2026, 6, 1))
        self.assertEqual(["境界。不自然。", "日時なし。不自然。"], [t.text for t in result.turns])

    def test_jsonl_files_in_nested_directories_belong_to_the_top_level_project(self) -> None:
        self.write_session("p/subagents", "agent-1", [human("不自然。", "2026-09-17T10:00:00Z")])
        [turn] = ClaudeCodeTranscriptSource(self.projects).scan(since=None).turns
        self.assertEqual("p", turn.project)
        self.assertEqual("agent-1", turn.session_id)

    def test_files_are_scanned_in_sorted_order(self) -> None:
        self.write_session("b", "s", [human("B。不自然。", "2026-09-17T10:00:00Z")])
        self.write_session("a", "s", [human("A。不自然。", "2026-09-17T10:00:00Z")])
        result = ClaudeCodeTranscriptSource(self.projects).scan(since=None)
        self.assertEqual(["A。不自然。", "B。不自然。"], [t.text for t in result.turns])
        self.assertEqual(2, result.stats.files_scanned)


class TestUnavailable(TranscriptCase):
    def test_missing_directory_raises(self) -> None:
        with self.assertRaises(TranscriptsUnavailable):
            ClaudeCodeTranscriptSource(self.projects / "missing").scan(since=None)

    def test_directory_without_jsonl_raises(self) -> None:
        (self.projects / "p").mkdir()
        (self.projects / "p" / "notes.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(TranscriptsUnavailable):
            ClaudeCodeTranscriptSource(self.projects).scan(since=None)


if __name__ == "__main__":
    unittest.main()
