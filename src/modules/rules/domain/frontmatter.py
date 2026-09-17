"""Frontmatter parsing for vault memory files (domain, standard library only).

The vault's own validator (`ai-memory` `scripts/validate_vault.py`) reads frontmatter
as flat `key: value` lines. Writing rules add fields under `metadata:`, so this parser
keeps one level of nesting: top-level scalar keys, plus the keys indented under
`metadata:`. Other nested blocks are ignored. Anything else raises FrontmatterError so
the caller can report a single parse failure (FR-013) instead of cascading findings.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

_FENCE = "---"
_LINE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z_][\w-]*):\s*(?P<value>.*)$")


class FrontmatterError(ValueError):
    """The document has no parseable frontmatter block."""


@dataclass(frozen=True)
class Frontmatter:
    fields: Mapping[str, str]
    metadata: Mapping[str, str]
    body: str


def parse_frontmatter(text: str) -> Frontmatter:
    if not text.startswith(_FENCE + "\n"):
        raise FrontmatterError("no frontmatter block at the start of the document")
    block, body = _split_block(text)

    fields: dict[str, str] = {}
    metadata: dict[str, str] = {}
    section: str | None = None
    for raw_line in block.splitlines():
        if not raw_line.strip():
            continue
        match = _LINE.match(raw_line)
        if match is None:
            raise FrontmatterError(f"cannot parse frontmatter line {raw_line.strip()[:40]!r}")
        key, value = match["key"], match["value"].strip()
        if match["indent"] == "":
            section = key if value == "" else None
            if value != "":
                fields[key] = value
        elif section == "metadata":
            metadata[key] = value
    return Frontmatter(fields, metadata, body)


def _split_block(text: str) -> tuple[str, str]:
    start = len(_FENCE) + 1
    end = text.find("\n" + _FENCE + "\n", start)
    if end != -1:
        return text[start:end], text[end + len(_FENCE) + 2 :]
    if text.endswith("\n" + _FENCE):
        return text[start : -len(_FENCE) - 1], ""
    raise FrontmatterError("frontmatter block is not closed")
