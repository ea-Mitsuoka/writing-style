"""Unit tests for the frontmatter parser edge cases not covered through validate_rule."""

from __future__ import annotations

import unittest

from src.modules.rules.domain.frontmatter import FrontmatterError, parse_frontmatter


class TestParseFrontmatter(unittest.TestCase):
    def test_block_closed_at_end_of_file_without_trailing_newline_has_empty_body(self) -> None:
        parsed = parse_frontmatter("---\nname: ja-term-a\nmetadata:\n  kind: term\n---")
        self.assertEqual({"name": "ja-term-a"}, dict(parsed.fields))
        self.assertEqual({"kind": "term"}, dict(parsed.metadata))
        self.assertEqual("", parsed.body)

    def test_keys_nested_under_another_block_are_not_treated_as_metadata(self) -> None:
        text = "---\nname: ja-term-a\nextra:\n  kind: style\nmetadata:\n  kind: term\n---\nbody\n"
        parsed = parse_frontmatter(text)
        self.assertEqual({"kind": "term"}, dict(parsed.metadata))
        self.assertEqual("body\n", parsed.body)

    def test_line_without_a_key_raises(self) -> None:
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("---\nname: ja-term-a\n- just a list item\n---\n")


if __name__ == "__main__":
    unittest.main()
