"""Integration tests for the extraction CLI: temp transcripts, captured streams, exit codes.

Exit codes, the single summary line, and the out-file rules are FR-111 … FR-113.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.modules.extraction.interface.cli import main


class CliCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.projects = self.root / "projects"
        (self.projects / "p").mkdir(parents=True)
        records = [
            {
                "type": "assistant",
                "timestamp": "2026-09-17T10:00:00Z",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "修正しました。"}],
                },
            },
            {
                "type": "user",
                "timestamp": "2026-09-17T10:01:00Z",
                "message": {"role": "user", "content": "この言い回しが不自然。"},
            },
        ]
        (self.projects / "p" / "s1.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
        )

    def run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        code = main(argv, stdout=out, stderr=err, today=date(2026, 9, 18))
        return code, out.getvalue(), err.getvalue()


class TestHappyPath(CliCase):
    def test_writes_the_report_and_prints_one_summary_line(self) -> None:
        out_file = self.root / "out" / "c.md"
        code, out, err = self.run_cli(
            ["--projects-dir", str(self.projects), "--out", str(out_file)]
        )
        self.assertEqual(0, code)
        self.assertEqual(1, len(out.splitlines()))
        self.assertIn("1 candidate(s)", out)
        self.assertIn(str(out_file), out)
        self.assertEqual("", err)
        report = out_file.read_text(encoding="utf-8")
        self.assertIn("# 指摘候補一覧", report)
        self.assertIn("スコア 6 — 2026-09-17 — p", report)
        self.assertIn("> この言い回しが不自然。", report)

    def test_excerpts_never_reach_stdout(self) -> None:
        code, out, _ = self.run_cli(
            ["--projects-dir", str(self.projects), "--out", str(self.root / "out" / "c.md")]
        )
        self.assertEqual(0, code)
        self.assertNotIn("不自然", out)

    def test_default_out_path_uses_the_generation_date_under_out(self) -> None:
        previous = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        code, out, _ = self.run_cli(["--projects-dir", str(self.projects)])
        self.assertEqual(0, code)
        self.assertTrue((self.root / "out" / "candidates-20260918.md").is_file())
        self.assertIn("out/candidates-20260918.md", out)

    def test_min_score_filters_candidates(self) -> None:
        code, out, _ = self.run_cli(
            [
                "--projects-dir",
                str(self.projects),
                "--out",
                str(self.root / "o.md"),
                "--min-score",
                "7",
            ]
        )
        self.assertEqual(0, code)
        self.assertIn("0 candidate(s)", out)

    def test_since_after_the_turn_excludes_it(self) -> None:
        code, out, _ = self.run_cli(
            [
                "--projects-dir",
                str(self.projects),
                "--out",
                str(self.root / "o.md"),
                "--since",
                "2026-09-18",
            ]
        )
        self.assertEqual(0, code)
        self.assertIn("0 candidate(s)", out)


class TestNoiseFromRealTranscripts(CliCase):
    """End-to-end cover for #12 over a fixture shaped like the real directory."""

    def write_session(self, project: str, session: str, records: list[dict]) -> None:
        directory = self.projects / project
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{session}.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
        )

    def test_continuation_summary_is_absent_and_a_replayed_turn_appears_once(self) -> None:
        summary = {
            "type": "user",
            "timestamp": "2026-09-17T09:00:00Z",
            "message": {
                "role": "user",
                "content": (
                    "This session is being continued from a previous conversation that ran "
                    "out of context.\n\nSummary:\n「表現が不自然」「言い回しがわかりづらい」"
                ),
            },
        }
        replayed = {
            "type": "user",
            "timestamp": "2026-09-17T10:01:00Z",
            "message": {"role": "user", "content": "この言い回しが不自然。"},
        }
        # s1 in project p already holds `replayed`; a resumed session and a renamed
        # project directory keep their own copies of it.
        self.write_session("p", "s2", [summary, replayed])
        self.write_session("p-renamed", "s3", [replayed])

        out_file = self.root / "o.md"
        code, out, _ = self.run_cli(["--projects-dir", str(self.projects), "--out", str(out_file)])

        self.assertEqual(0, code)
        self.assertIn("1 candidate(s)", out)
        report = out_file.read_text(encoding="utf-8")
        self.assertNotIn("This session is being continued", report)
        self.assertIn("`s1`（同一発話: `s2`, `s3`）", report)


class TestUsageErrors(CliCase):
    def test_existing_out_file_is_not_overwritten(self) -> None:
        out_file = self.root / "o.md"
        out_file.write_text("keep me", encoding="utf-8")
        code, _, err = self.run_cli(["--projects-dir", str(self.projects), "--out", str(out_file)])
        self.assertEqual(2, code)
        self.assertIn("already exists", err)
        self.assertEqual("keep me", out_file.read_text(encoding="utf-8"))

    def test_missing_projects_dir_exits_2(self) -> None:
        code, _, err = self.run_cli(
            ["--projects-dir", str(self.root / "nowhere"), "--out", str(self.root / "o.md")]
        )
        self.assertEqual(2, code)
        self.assertIn("nowhere", err)

    def test_invalid_since_exits_2(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            self.run_cli(["--projects-dir", str(self.projects), "--since", "yesterday"])
        self.assertEqual(2, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
