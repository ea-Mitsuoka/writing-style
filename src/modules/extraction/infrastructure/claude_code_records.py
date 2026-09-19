"""Interpretation of one Claude Code transcript record (infrastructure, pure functions).

This is the only place that knows the JSONL record shape (docs/requirements/extraction.md
A-1, surveyed 2026-09-18). Everything here takes a decoded record and returns plain text
or None, so the rules FR-102 / FR-103 are unit-testable without files, and a format
change stays inside this module (ADR-0002).
"""

from __future__ import annotations

import re
from typing import Any

# Harness-inserted blocks such as <system-reminder>…</system-reminder> and local command
# echoes (<command-name>…</command-name>) are not the human's words (FR-103).
_EMBEDDED_BLOCK = re.compile(r"<([a-z][a-z0-9-]*)>.*?</\1>", re.S)

# When a session runs out of context the harness writes its summary of the earlier turns
# as a user record. It quotes the corrections it summarizes, so it scores high while
# containing nothing new; only a turn that *starts* with this wording is the summary
# itself (FR-102).
_CONTINUATION_SUMMARY_PREFIX = "This session is being continued from a previous conversation"


def human_text(record: dict[str, Any]) -> str | None:
    """The human's own text for a user record, or None when the record is not a human turn."""
    if record.get("type") != "user" or record.get("isMeta") or record.get("isSidechain"):
        return None
    message = record.get("message")
    if not isinstance(message, dict) or message.get("role") != "user":
        return None
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(_block_type(block) == "tool_result" for block in content):
            return None
        text = _join_text_blocks(content)
    else:
        return None
    cleaned = _EMBEDDED_BLOCK.sub("", text).strip()
    if not cleaned or cleaned.startswith(_CONTINUATION_SUMMARY_PREFIX):
        return None
    return cleaned


def assistant_text(record: dict[str, Any]) -> str | None:
    """The assistant's visible text for an assistant record (thinking and tool blocks excluded)."""
    if record.get("type") != "assistant":
        return None
    message = record.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = _join_text_blocks(content)
    else:
        return None
    return text.strip() or None


def record_timestamp(record: dict[str, Any]) -> str | None:
    timestamp = record.get("timestamp")
    return timestamp if isinstance(timestamp, str) else None


def _block_type(block: Any) -> str | None:
    return block.get("type") if isinstance(block, dict) else None


def _join_text_blocks(blocks: list[Any]) -> str:
    texts = [
        block.get("text", "")
        for block in blocks
        if _block_type(block) == "text" and isinstance(block.get("text"), str)
    ]
    return "\n".join(text for text in texts if text)
