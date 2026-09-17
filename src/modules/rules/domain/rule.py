"""Writing-rule format checks (domain, standard library only).

The format is defined by the vault `ea-Mitsuoka/ai-memory` in `AGENTS.md`「表現ルール」
(2026-09-18) and restated as FR-002 … FR-013 in docs/requirements.md. Each finding
carries the requirement id it violates, so a report line is traceable without this
module's source. Invalid input is a finding, not an exception: the interface layer only
has to print what it gets (COD-011).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import PurePosixPath

from .frontmatter import Frontmatter, FrontmatterError, parse_frontmatter

KINDS: tuple[str, ...] = ("term", "style", "structure")

# The scope vocabulary exists in code only here. Source of truth: the vault AGENTS.md
# 「表現ルール」scope table (2026-09-18). Change both in the same change (ADR-0001).
SCOPE_TAGS: tuple[str, ...] = (
    "customer-doc",
    "decision-doc",
    "internal-doc",
    "slide",
    "chat",
    "code",
)

RULE_HEADING = "## ルール"
NG_OK_HEADING = "## NG / OK"
WHY_MARKER = "**Why:**"
HOW_MARKER = "**How to apply:**"

_NAME = re.compile(r"^ja-(?P<kind>term|style|structure)-[a-z0-9]+(?:-[a-z0-9]+)*$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SCOPE_LIST = re.compile(r"^\[(?P<items>.*)\]$")
_TABLE_SEPARATOR_CELL = re.compile(r"^:?-+:?$")


@dataclass(frozen=True)
class Finding:
    path: str
    code: str
    message: str


Check = Callable[[str, Frontmatter], tuple[str, str] | None]


def validate_rule(path: str, text: str) -> tuple[Finding, ...]:
    """Return one finding per violated requirement, in requirement-id order."""
    try:
        frontmatter = parse_frontmatter(text)
    except FrontmatterError as error:
        return (Finding(path, "FR-013", f"frontmatter cannot be parsed: {error}"),)

    stem = PurePosixPath(path).stem
    findings: list[Finding] = []
    for check in _CHECKS:
        result = check(stem, frontmatter)
        if result is not None:
            code, message = result
            findings.append(Finding(path, code, message))
    return tuple(findings)


def _check_name(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    if _NAME.match(stem) is None:
        return "FR-002", f"file name {stem!r} must match ja-<term|style|structure>-<slug>"
    name = frontmatter.fields.get("name")
    if name != stem:
        return "FR-002", f"frontmatter name {name!r} must equal the file name {stem!r}"
    return None


def _check_kind(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    kind = frontmatter.metadata.get("kind")
    if kind not in KINDS:
        return "FR-003", f"metadata.kind {kind!r} must be one of {', '.join(KINDS)}"
    match = _NAME.match(stem)
    if match is not None and match["kind"] != kind:
        return "FR-003", f"metadata.kind {kind!r} must equal the kind in the file name"
    return None


def _check_type(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    memory_type = frontmatter.metadata.get("type")
    if memory_type != "feedback":
        return "FR-004", f"metadata.type {memory_type!r} must be 'feedback'"
    return None


def _check_scope(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    raw = frontmatter.metadata.get("scope")
    if raw is None:
        return "FR-005", "metadata.scope is required: [tag, ...] with at least one tag"
    match = _SCOPE_LIST.match(raw)
    if match is None:
        return "FR-005", f"metadata.scope {raw!r} must be a bracketed list: [tag, ...]"
    tags = [tag.strip() for tag in match["items"].split(",") if tag.strip()]
    if not tags:
        return "FR-005", "metadata.scope must list at least one tag"
    unknown = [tag for tag in tags if tag not in SCOPE_TAGS]
    if unknown:
        return "FR-005", f"unknown scope tag(s) {unknown!r}; allowed: {', '.join(SCOPE_TAGS)}"
    if len(set(tags)) != len(tags):
        return "FR-005", f"metadata.scope repeats a tag: {tags!r}"
    return None


def _check_updated(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    updated = frontmatter.fields.get("updated")
    if updated is None or _ISO_DATE.match(updated) is None:
        return "FR-006", f"updated {updated!r} must be a YYYY-MM-DD date"
    try:
        date.fromisoformat(updated)
    except ValueError:
        return "FR-006", f"updated {updated!r} is not an existing calendar date"
    return None


def _check_description(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    if not frontmatter.fields.get("description", "").strip():
        return "FR-007", "description must not be empty"
    return None


def _check_headings(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    rule_at = _heading_positions(frontmatter.body, RULE_HEADING)
    ng_ok_at = _heading_positions(frontmatter.body, NG_OK_HEADING)
    if len(rule_at) != 1 or len(ng_ok_at) != 1 or rule_at[0] >= ng_ok_at[0]:
        return (
            "FR-008",
            f"body must contain '{RULE_HEADING}' once, then '{NG_OK_HEADING}' once, in that order",
        )
    return None


def _check_ng_ok_pairs(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    positions = _heading_positions(frontmatter.body, NG_OK_HEADING)
    if len(positions) != 1:
        return None  # FR-008 already reports the heading problem.
    if _complete_pairs(_section_lines(frontmatter.body, positions[0])) == 0:
        return "FR-009", f"'{NG_OK_HEADING}' needs a table with at least one row filling both cells"
    return None


def _check_why_how(stem: str, frontmatter: Frontmatter) -> tuple[str, str] | None:
    missing = [marker for marker in (WHY_MARKER, HOW_MARKER) if marker not in frontmatter.body]
    if missing:
        return "FR-010", f"body must contain {' and '.join(missing)}"
    return None


_CHECKS: tuple[Check, ...] = (
    _check_name,
    _check_kind,
    _check_type,
    _check_scope,
    _check_updated,
    _check_description,
    _check_headings,
    _check_ng_ok_pairs,
    _check_why_how,
)


def _heading_positions(body: str, heading: str) -> list[int]:
    return [index for index, line in enumerate(body.splitlines()) if line.strip() == heading]


def _section_lines(body: str, heading_index: int) -> list[str]:
    lines = body.splitlines()[heading_index + 1 :]
    section: list[str] = []
    for line in lines:
        if line.startswith("## "):
            break
        section.append(line)
    return section


def _complete_pairs(section: list[str]) -> int:
    rows = [_cells(line) for line in section if line.lstrip().startswith("|")]
    data_rows = [
        cells
        for cells in rows[1:]  # the first table row is the header
        if not all(_TABLE_SEPARATOR_CELL.match(cell) for cell in cells if cell)
    ]
    return sum(1 for cells in data_rows if len(cells) >= 2 and cells[0] and cells[1])


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [cell.strip() for cell in inner.split("|")]
