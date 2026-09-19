"""Markdown rendering of the candidate list (domain, pure).

Layout per docs/requirements/extraction.md FR-110. The report may contain personal and
customer names, so the interface layer writes it only under `out/` (C-1); this function
just returns text.
"""

from __future__ import annotations

from collections.abc import Sequence

from .candidate import Candidate, ScanStats

TURN_EXCERPT_CHARS = 400
ASSISTANT_EXCERPT_CHARS = 200
NO_ASSISTANT_TEXT = "（直前の assistant 本文なし）"
UNKNOWN_DATE = "不明"


def render_report(
    candidates: Sequence[Candidate],
    stats: ScanStats,
    *,
    generated_at: str,
    projects_dir: str,
    since: str | None,
    min_score: int,
) -> str:
    lines = [
        "# 指摘候補一覧",
        "",
        "| 項目 | 値 |",
        "| -- | -- |",
        f"| 生成日時 | {generated_at} |",
        f"| 対象ディレクトリ | `{projects_dir}` |",
        f"| 期間 | {since + ' 以降' if since else '全期間'} |",
        f"| スコア下限 | {min_score} |",
        f"| 走査ファイル数 | {stats.files_scanned} |",
        f"| 人間の発話数 | {stats.human_turns} |",
        f"| 読み飛ばし行数 | {stats.skipped_lines} |",
        f"| 候補数 | {len(candidates)} |",
        "",
        "このファイルは人名・案件名を含み得る。commit も共有もしない"
        "（docs/requirements/extraction.md C-1）。仕分けが終わったら削除してよい。",
        "",
    ]
    for index, candidate in enumerate(candidates, 1):
        lines.extend(_candidate_section(index, candidate))
    return "\n".join(lines).rstrip("\n") + "\n"


def _candidate_section(index: int, candidate: Candidate) -> list[str]:
    turn = candidate.turn
    date = turn.timestamp[:10] if turn.timestamp else UNKNOWN_DATE
    assistant = _excerpt(turn.preceding_assistant, ASSISTANT_EXCERPT_CHARS)
    return [
        f"## {index}. スコア {candidate.score} — {date} — {turn.project}",
        "",
        f"- セッション: {_sessions(candidate)}",
        f"- キーワード: {', '.join(candidate.keywords)}",
        "",
        "### 発話",
        "",
        _quote(_excerpt(turn.text, TURN_EXCERPT_CHARS)),
        "",
        "### 直前の assistant 本文",
        "",
        _quote(assistant) if assistant else NO_ASSISTANT_TEXT,
        "",
    ]


def _sessions(candidate: Candidate) -> str:
    """The session that kept the turn, plus the sessions that replayed it (FR-114)."""
    session = f"`{candidate.turn.session_id}`"
    if not candidate.duplicate_sessions:
        return session
    others = ", ".join(f"`{s}`" for s in candidate.duplicate_sessions)
    return f"{session}（同一発話: {others}）"


def _excerpt(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


def _quote(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines()) or ">"
