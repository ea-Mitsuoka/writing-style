"""Integration tests for the filesystem RuleSource adapter (real files in a temp dir).

Each test builds its own vault layout, so no state is shared and no fixture file has to
be opened to read the test (TST-010).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.modules.rules.infrastructure.filesystem_rule_source import (
    FilesystemRuleSource,
    VaultLayoutError,
)


class TestFilesystemRuleSource(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault = Path(self._tmp.name)
        self.rules_dir = self.vault / "30_memory" / "feedback"
        self.rules_dir.mkdir(parents=True)

    def write(self, name: str, text: str = "# stub\n") -> None:
        (self.rules_dir / name).write_text(text, encoding="utf-8")

    def test_only_ja_markdown_files_directly_under_feedback_are_selected(self) -> None:
        self.write("ja-term-b.md")
        self.write("ja-style-a.md")
        self.write("other-feedback.md")
        self.write("ja-notes.txt")
        (self.rules_dir / "nested").mkdir()
        (self.rules_dir / "nested" / "ja-term-c.md").write_text("# stub\n", encoding="utf-8")

        documents = FilesystemRuleSource(self.vault).rule_documents()

        self.assertEqual(
            ["30_memory/feedback/ja-style-a.md", "30_memory/feedback/ja-term-b.md"],
            [document.path for document in documents],
        )

    def test_document_text_is_the_utf8_file_content(self) -> None:
        self.write("ja-term-a.md", "---\nname: ja-term-a\n---\n## ルール\n")

        [document] = FilesystemRuleSource(self.vault).rule_documents()

        self.assertEqual("---\nname: ja-term-a\n---\n## ルール\n", document.text)
        self.assertIsNone(document.read_error)

    def test_invalid_utf8_file_is_returned_with_a_read_error(self) -> None:
        (self.rules_dir / "ja-term-broken.md").write_bytes(b"---\n\xff\xfe\n---\n")

        [document] = FilesystemRuleSource(self.vault).rule_documents()

        self.assertIsNone(document.text)
        self.assertIn("UTF-8", document.read_error or "")

    def test_missing_feedback_directory_raises_vault_layout_error(self) -> None:
        empty_vault = self.vault / "elsewhere"
        empty_vault.mkdir()

        with self.assertRaises(VaultLayoutError):
            FilesystemRuleSource(empty_vault).rule_documents()

    def test_empty_feedback_directory_yields_no_documents(self) -> None:
        self.assertEqual([], FilesystemRuleSource(self.vault).rule_documents())


if __name__ == "__main__":
    unittest.main()
