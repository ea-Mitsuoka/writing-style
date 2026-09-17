"""Integration tests for the rules CLI: real temp-dir vaults, captured streams, exit codes.

Exit codes and the output line format are the FR-011 / FR-012 specification, not values
read back from the implementation (TST-010).
"""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from src.modules.rules.interface.cli import main

from tests.modules.rules.unit.builders import prototype_rule, rule_text


class CliCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault = Path(self._tmp.name)
        (self.vault / "30_memory" / "feedback").mkdir(parents=True)

    def write_rule(self, name: str, text: str) -> None:
        (self.vault / "30_memory" / "feedback" / name).write_text(text, encoding="utf-8")

    def run_cli(
        self, argv: list[str], environ: dict[str, str] | None = None
    ) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        code = main(argv, environ if environ is not None else {}, out, err)
        return code, out.getvalue(), err.getvalue()


class TestVaultResolution(CliCase):
    def test_without_vault_argument_or_environment_exits_2_with_the_reason(self) -> None:
        code, out, err = self.run_cli([])
        self.assertEqual(2, code)
        self.assertIn("OBSIDIAN_VAULT_PATH", err)
        self.assertEqual("", out)

    def test_environment_variable_supplies_the_vault_path(self) -> None:
        self.write_rule("ja-term-gc-iam-roles.md", prototype_rule())
        code, _, _ = self.run_cli([], {"OBSIDIAN_VAULT_PATH": str(self.vault)})
        self.assertEqual(0, code)

    def test_argument_takes_precedence_over_the_environment(self) -> None:
        self.write_rule("ja-term-gc-iam-roles.md", prototype_rule())
        code, _, _ = self.run_cli(
            ["--vault", str(self.vault)], {"OBSIDIAN_VAULT_PATH": "/nonexistent"}
        )
        self.assertEqual(0, code)

    def test_nonexistent_vault_path_exits_2(self) -> None:
        code, _, err = self.run_cli(["--vault", str(self.vault / "missing")])
        self.assertEqual(2, code)
        self.assertIn("not a directory", err)

    def test_vault_without_feedback_directory_exits_2(self) -> None:
        bare = self.vault / "bare"
        bare.mkdir()
        code, _, err = self.run_cli(["--vault", str(bare)])
        self.assertEqual(2, code)
        self.assertIn("30_memory/feedback", err)


class TestReporting(CliCase):
    def test_conforming_vault_prints_no_findings_and_exits_0(self) -> None:
        self.write_rule("ja-term-gc-iam-roles.md", prototype_rule())
        code, out, err = self.run_cli(["--vault", str(self.vault)])
        self.assertEqual(0, code)
        self.assertEqual("", out)
        self.assertIn("checked 1 rule file(s), 0 finding(s)", err)

    def test_findings_are_one_line_each_as_path_code_message_and_exit_1(self) -> None:
        self.write_rule("ja-term-gc-iam-roles.md", rule_text(type="reference", scope=None))
        code, out, _ = self.run_cli(["--vault", str(self.vault)])
        self.assertEqual(1, code)
        lines = out.splitlines()
        self.assertEqual(2, len(lines))
        self.assertTrue(lines[0].startswith("30_memory/feedback/ja-term-gc-iam-roles.md:FR-004:"))
        self.assertTrue(lines[1].startswith("30_memory/feedback/ja-term-gc-iam-roles.md:FR-005:"))

    def test_empty_feedback_directory_prints_a_notice_and_exits_0(self) -> None:
        code, out, _ = self.run_cli(["--vault", str(self.vault)])
        self.assertEqual(0, code)
        self.assertIn("no rule files found", out)


if __name__ == "__main__":
    unittest.main()
