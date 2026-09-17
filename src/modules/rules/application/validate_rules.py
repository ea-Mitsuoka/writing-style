"""Rules application — the ValidateRules use case.

Orchestrates the domain over every document a RuleSource yields; holds no format rules
of its own (those live in `domain/rule.py`).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.rule import Finding, validate_rule
from .ports import RuleSource


@dataclass(frozen=True)
class Report:
    findings: tuple[Finding, ...]
    checked: int


class ValidateRules:
    def __init__(self, source: RuleSource) -> None:
        self._source = source

    def handle(self) -> Report:
        findings: list[Finding] = []
        checked = 0
        for document in self._source.rule_documents():
            checked += 1
            if document.text is None:
                findings.append(
                    Finding(
                        document.path,
                        "FR-013",
                        f"document could not be read: {document.read_error}",
                    )
                )
                continue
            findings.extend(validate_rule(document.path, document.text))
        return Report(tuple(findings), checked)
