"""Rules infrastructure — filesystem adapter implementing the RuleSource port.

Reads `30_memory/feedback/ja-*.md` directly under a vault checkout (FR-001) and never
writes. An unreadable file becomes a RuleDocument with `read_error` so the use case can
report it instead of the adapter hiding it (COD-010). A vault without the expected layout
is a usage error surfaced as VaultLayoutError before any file is read.
"""

from __future__ import annotations

from pathlib import Path

from ..application.ports import RuleDocument

RULES_DIR = Path("30_memory") / "feedback"
RULE_GLOB = "ja-*.md"


class VaultLayoutError(Exception):
    """The vault root does not contain `30_memory/feedback/`."""


class FilesystemRuleSource:
    def __init__(self, vault_root: Path) -> None:
        self._root = vault_root

    def rule_documents(self) -> list[RuleDocument]:
        directory = self._root / RULES_DIR
        if not directory.is_dir():
            raise VaultLayoutError(
                f"{directory} is not a directory; expected the vault layout "
                f"<vault>/{RULES_DIR.as_posix()}"
            )
        return [self._read(path) for path in sorted(directory.glob(RULE_GLOB)) if path.is_file()]

    def _read(self, path: Path) -> RuleDocument:
        relative = path.relative_to(self._root).as_posix()
        try:
            return RuleDocument(relative, path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as error:
            return RuleDocument(relative, None, read_error=f"not valid UTF-8: {error.reason}")
        except OSError as error:
            return RuleDocument(relative, None, read_error=f"cannot read file: {error.strerror}")
