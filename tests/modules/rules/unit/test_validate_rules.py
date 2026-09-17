"""Unit tests for the ValidateRules use case (application).

The rule source is a fake implementing the RuleSource port (TST-020), so these tests
run without I/O and observe the use case through its public seam only.
"""

from __future__ import annotations

import unittest

from src.modules.rules.application.ports import RuleDocument
from src.modules.rules.application.validate_rules import ValidateRules

from .builders import PROTOTYPE_PATH, prototype_rule, rule_text


class FakeRuleSource:
    def __init__(self, documents: list[RuleDocument]) -> None:
        self._documents = documents

    def rule_documents(self) -> list[RuleDocument]:
        return list(self._documents)


class TestValidateRules(unittest.TestCase):
    def test_empty_source_yields_an_empty_report(self) -> None:
        report = ValidateRules(FakeRuleSource([])).handle()
        self.assertEqual((), report.findings)
        self.assertEqual(0, report.checked)

    def test_conforming_document_yields_no_findings_and_is_counted(self) -> None:
        source = FakeRuleSource([RuleDocument(PROTOTYPE_PATH, prototype_rule())])
        report = ValidateRules(source).handle()
        self.assertEqual((), report.findings)
        self.assertEqual(1, report.checked)

    def test_findings_from_every_document_are_collected_in_source_order(self) -> None:
        second = "30_memory/feedback/ja-style-keigo.md"
        source = FakeRuleSource(
            [
                RuleDocument(PROTOTYPE_PATH, rule_text(type="reference")),
                RuleDocument(second, rule_text(name="ja-style-keigo", kind="style", scope=None)),
            ]
        )
        report = ValidateRules(source).handle()
        self.assertEqual(
            [(PROTOTYPE_PATH, "FR-004"), (second, "FR-005")],
            [(finding.path, finding.code) for finding in report.findings],
        )
        self.assertEqual(2, report.checked)

    def test_unreadable_document_is_reported_once_as_a_parse_failure(self) -> None:
        unreadable = RuleDocument(PROTOTYPE_PATH, None, read_error="not valid UTF-8")
        report = ValidateRules(FakeRuleSource([unreadable])).handle()
        self.assertEqual(["FR-013"], [finding.code for finding in report.findings])
        self.assertIn("not valid UTF-8", report.findings[0].message)
        self.assertEqual(1, report.checked)


if __name__ == "__main__":
    unittest.main()
