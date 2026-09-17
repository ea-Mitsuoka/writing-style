"""Rules application ports — the interface this module depends on.

Defined here, implemented in `infrastructure/` (dependency inversion, ARC-002). The use
case never touches the filesystem; a source adapter yields documents, and an unreadable
file arrives as a document with `text=None` and a `read_error` so the use case can report
it without swallowing the failure (COD-010).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RuleDocument:
    """One candidate rule file: its vault-relative POSIX path and its text, or the
    reason it could not be read."""

    path: str
    text: str | None
    read_error: str | None = None


class RuleSource(Protocol):
    def rule_documents(self) -> Iterable[RuleDocument]: ...
