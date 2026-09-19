"""Unit tests for interpreting one Claude Code transcript record (pure functions, no I/O).

Record shapes come from the 2026-09-18 survey of `~/.claude/projects/**/*.jsonl`
(docs/requirements/extraction.md A-1); the selection rules are FR-102 / FR-103.
"""

from __future__ import annotations

import unittest

from src.modules.extraction.infrastructure.claude_code_records import (
    assistant_text,
    human_text,
    record_timestamp,
)


def user_record(content, **flags):
    return {"type": "user", "message": {"role": "user", "content": content}, **flags}


def assistant_record(content):
    return {"type": "assistant", "message": {"role": "assistant", "content": content}}


class TestHumanText(unittest.TestCase):
    def test_string_content_is_returned_stripped(self) -> None:
        self.assertEqual("この表現は不自然。", human_text(user_record("  この表現は不自然。\n")))

    def test_text_blocks_are_joined(self) -> None:
        record = user_record(
            [{"type": "text", "text": "一行目"}, {"type": "text", "text": "二行目"}]
        )
        self.assertEqual("一行目\n二行目", human_text(record))

    def test_tool_result_content_is_not_a_human_turn(self) -> None:
        record = user_record([{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}])
        self.assertIsNone(human_text(record))

    def test_meta_record_is_not_a_human_turn(self) -> None:
        self.assertIsNone(human_text(user_record("不自然。", isMeta=True)))

    def test_sidechain_record_is_not_a_human_turn(self) -> None:
        self.assertIsNone(human_text(user_record("不自然。", isSidechain=True)))

    def test_assistant_record_is_not_a_human_turn(self) -> None:
        self.assertIsNone(human_text(assistant_record([{"type": "text", "text": "はい"}])))

    def test_record_whose_message_role_is_not_user_is_skipped(self) -> None:
        record = {"type": "user", "message": {"role": "assistant", "content": "不自然。"}}
        self.assertIsNone(human_text(record))

    def test_embedded_tag_blocks_are_removed(self) -> None:
        text = "<system-reminder>\nInternal note.\n</system-reminder>\nここが不自然。"
        self.assertEqual("ここが不自然。", human_text(user_record(text)))

    def test_local_command_blocks_are_removed(self) -> None:
        text = (
            "<command-name>/model</command-name>\n"
            "<command-message>model</command-message>\n言い回しを直して"
        )
        self.assertEqual("言い回しを直して", human_text(user_record(text)))

    def test_turn_that_is_only_embedded_blocks_is_skipped(self) -> None:
        text = "<system-reminder>only this</system-reminder>"
        self.assertIsNone(human_text(user_record(text)))

    def test_record_without_message_is_skipped(self) -> None:
        self.assertIsNone(human_text({"type": "user"}))

    def test_harness_continuation_summary_is_not_a_human_turn(self) -> None:
        # The harness writes the summary of a context-exhausted session as a user record;
        # it quotes the earlier turns, so it scores high while saying nothing new (#12).
        text = (
            "This session is being continued from a previous conversation that ran out "
            "of context. The summary below covers the earlier portion of the conversation.\n"
            "\nSummary:\n1. Primary Request and Intent:\n   「表現が不自然」と指摘された。"
        )
        self.assertIsNone(human_text(user_record(text)))

    def test_continuation_summary_after_an_embedded_block_is_still_skipped(self) -> None:
        text = (
            "<system-reminder>note</system-reminder>\n"
            "This session is being continued from a previous conversation. 表現が不自然。"
        )
        self.assertIsNone(human_text(user_record(text)))

    def test_turn_that_merely_mentions_the_continuation_wording_is_kept(self) -> None:
        text = "ログに This session is being continued from a previous conversation と出る理由は？"
        self.assertEqual(text, human_text(user_record(text)))


class TestAssistantText(unittest.TestCase):
    def test_text_blocks_are_joined_and_other_blocks_ignored(self) -> None:
        record = assistant_record(
            [
                {"type": "thinking", "thinking": "..."},
                {"type": "text", "text": "修正しました。"},
                {"type": "tool_use", "id": "t1", "name": "Edit", "input": {}},
                {"type": "text", "text": "どうですか。"},
            ]
        )
        self.assertEqual("修正しました。\nどうですか。", assistant_text(record))

    def test_string_content_is_returned(self) -> None:
        self.assertEqual("はい。", assistant_text(assistant_record("はい。")))

    def test_assistant_record_without_text_yields_none(self) -> None:
        record = assistant_record([{"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}])
        self.assertIsNone(assistant_text(record))

    def test_user_record_yields_none(self) -> None:
        self.assertIsNone(assistant_text(user_record("不自然。")))


class TestRecordTimestamp(unittest.TestCase):
    def test_timestamp_string_is_returned(self) -> None:
        self.assertEqual(
            "2026-09-17T14:40:04.123Z",
            record_timestamp({"timestamp": "2026-09-17T14:40:04.123Z"}),
        )

    def test_missing_or_non_string_timestamp_is_none(self) -> None:
        self.assertIsNone(record_timestamp({}))
        self.assertIsNone(record_timestamp({"timestamp": 1700000000}))


if __name__ == "__main__":
    unittest.main()
