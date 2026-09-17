"""Unit tests for the writing-rule format checks (domain).

One behavior per test; the finding code is the requirement id from docs/requirements.md
(FR-002 … FR-013), so a failing test name plus its code identifies the broken rule.
Expected values come from the vault `AGENTS.md` "表現ルール" section (2026-09-18), not
from the implementation (TST-010).
"""

from __future__ import annotations

import unittest

from src.modules.rules.domain.rule import SCOPE_TAGS, Finding, validate_rule

from .builders import NG_OK_SECTION, PROTOTYPE_PATH, prototype_rule, rule_text


def codes(findings: tuple[Finding, ...]) -> list[str]:
    return [finding.code for finding in findings]


class TestConformingRule(unittest.TestCase):
    def test_prototype_rule_has_no_findings(self) -> None:
        self.assertEqual((), validate_rule(PROTOTYPE_PATH, prototype_rule()))

    def test_scope_vocabulary_matches_the_vault_agents_md(self) -> None:
        # Literal from ea-Mitsuoka/ai-memory AGENTS.md「表現ルール」(2026-09-18).
        self.assertEqual(
            ("customer-doc", "decision-doc", "internal-doc", "slide", "chat", "code"),
            SCOPE_TAGS,
        )


class TestNaming(unittest.TestCase):
    def test_filename_outside_the_ja_pattern_is_reported(self) -> None:
        path = "30_memory/feedback/ja-glossary-gc.md"
        findings = validate_rule(path, rule_text(name="ja-glossary-gc"))
        self.assertIn("FR-002", codes(findings))

    def test_name_differing_from_filename_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(name="ja-term-other"))
        self.assertEqual(["FR-002"], codes(findings))

    def test_uppercase_in_slug_is_reported(self) -> None:
        path = "30_memory/feedback/ja-term-GC-roles.md"
        findings = validate_rule(path, rule_text(name="ja-term-GC-roles"))
        self.assertIn("FR-002", codes(findings))

    def test_finding_carries_the_document_path(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(name="ja-term-other"))
        self.assertEqual(PROTOTYPE_PATH, findings[0].path)


class TestKind(unittest.TestCase):
    def test_kind_not_matching_the_filename_kind_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(kind="style"))
        self.assertEqual(["FR-003"], codes(findings))

    def test_unknown_kind_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(kind="glossary"))
        self.assertEqual(["FR-003"], codes(findings))

    def test_missing_kind_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(kind=None))
        self.assertEqual(["FR-003"], codes(findings))


class TestType(unittest.TestCase):
    def test_type_other_than_feedback_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(type="reference"))
        self.assertEqual(["FR-004"], codes(findings))


class TestScope(unittest.TestCase):
    def test_missing_scope_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(scope=None))
        self.assertEqual(["FR-005"], codes(findings))

    def test_empty_scope_list_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(scope="[]"))
        self.assertEqual(["FR-005"], codes(findings))

    def test_unknown_scope_tag_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(scope="[customer-doc, email]"))
        self.assertEqual(["FR-005"], codes(findings))

    def test_duplicate_scope_tag_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(scope="[slide, slide]"))
        self.assertEqual(["FR-005"], codes(findings))

    def test_scope_without_brackets_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(scope="customer-doc, slide"))
        self.assertEqual(["FR-005"], codes(findings))

    def test_single_valid_tag_is_accepted(self) -> None:
        self.assertEqual((), validate_rule(PROTOTYPE_PATH, rule_text(scope="[chat]")))


class TestUpdated(unittest.TestCase):
    def test_non_existent_calendar_date_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(updated="2026-02-30"))
        self.assertEqual(["FR-006"], codes(findings))

    def test_date_in_another_format_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(updated="2026/09/18"))
        self.assertEqual(["FR-006"], codes(findings))

    def test_missing_updated_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(updated=None))
        self.assertEqual(["FR-006"], codes(findings))


class TestDescription(unittest.TestCase):
    def test_empty_description_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(description=""))
        self.assertEqual(["FR-007"], codes(findings))

    def test_missing_description_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(description=None))
        self.assertEqual(["FR-007"], codes(findings))


class TestBodyHeadings(unittest.TestCase):
    def test_missing_rule_heading_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(rule="本文だけで見出しがない。\n"))
        self.assertEqual(["FR-008"], codes(findings))

    def test_missing_ng_ok_heading_is_reported(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(ng_ok=""))
        self.assertEqual(["FR-008"], codes(findings))

    def test_ng_ok_before_rule_is_reported(self) -> None:
        swapped = rule_text(rule=NG_OK_SECTION, ng_ok="## ルール\n\n規則本体。\n")
        self.assertEqual(["FR-008"], codes(validate_rule(PROTOTYPE_PATH, swapped)))

    def test_duplicate_ng_ok_heading_is_reported(self) -> None:
        doubled = rule_text(ng_ok=NG_OK_SECTION + "\n" + NG_OK_SECTION)
        self.assertEqual(["FR-008"], codes(validate_rule(PROTOTYPE_PATH, doubled)))


class TestNgOkPairs(unittest.TestCase):
    def test_table_without_data_rows_is_reported(self) -> None:
        header_only = "## NG / OK\n\n| NG | OK |\n|----|----|\n"
        findings = validate_rule(PROTOTYPE_PATH, rule_text(ng_ok=header_only))
        self.assertEqual(["FR-009"], codes(findings))

    def test_row_with_an_empty_ok_cell_does_not_count(self) -> None:
        half = "## NG / OK\n\n| NG | OK |\n|----|----|\n| 閲覧者ロール |  |\n"
        findings = validate_rule(PROTOTYPE_PATH, rule_text(ng_ok=half))
        self.assertEqual(["FR-009"], codes(findings))

    def test_section_without_a_table_is_reported(self) -> None:
        prose = "## NG / OK\n\n例はあとで書く。\n"
        findings = validate_rule(PROTOTYPE_PATH, rule_text(ng_ok=prose))
        self.assertEqual(["FR-009"], codes(findings))

    def test_one_complete_pair_is_enough(self) -> None:
        one_pair = (
            "## NG / OK\n\n| NG | OK |\n|----|----|\n"
            "| 閲覧者（roles/browser） | ブラウザ（roles/browser） |\n"
        )
        self.assertEqual((), validate_rule(PROTOTYPE_PATH, rule_text(ng_ok=one_pair)))


class TestWhyAndHowToApply(unittest.TestCase):
    def test_missing_why_is_reported(self) -> None:
        only_how = "**How to apply:** 表示名 + ロール ID の形にする。\n"
        findings = validate_rule(PROTOTYPE_PATH, rule_text(why_how=only_how))
        self.assertEqual(["FR-010"], codes(findings))

    def test_missing_how_to_apply_is_reported(self) -> None:
        only_why = "**Why:** 画面の表示名と照合できるようにする。\n"
        findings = validate_rule(PROTOTYPE_PATH, rule_text(why_how=only_why))
        self.assertEqual(["FR-010"], codes(findings))


class TestUnparseableDocument(unittest.TestCase):
    def test_missing_frontmatter_reports_only_the_parse_failure(self) -> None:
        findings = validate_rule(PROTOTYPE_PATH, rule_text(frontmatter="# 見出しだけ\n"))
        self.assertEqual(["FR-013"], codes(findings))

    def test_unterminated_frontmatter_reports_only_the_parse_failure(self) -> None:
        open_block = "---\nname: ja-term-gc-iam-roles\nmetadata:\n  type: feedback\n"
        findings = validate_rule(PROTOTYPE_PATH, rule_text(frontmatter=open_block))
        self.assertEqual(["FR-013"], codes(findings))


class TestMultipleViolations(unittest.TestCase):
    def test_each_violated_requirement_is_reported_once(self) -> None:
        text = rule_text(type="reference", scope=None, updated="today", why_how="")
        self.assertEqual(
            ["FR-004", "FR-005", "FR-006", "FR-010"],
            codes(validate_rule(PROTOTYPE_PATH, text)),
        )


if __name__ == "__main__":
    unittest.main()
