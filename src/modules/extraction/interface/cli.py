"""Extraction interface — command-line entry point and composition root.

    python3 -m src.modules.extraction.interface.cli [--projects-dir DIR] [--since YYYY-MM-DD]
        [--min-score N] [--out FILE]

Writes the candidate report to `--out` (default `out/candidates-<YYYYMMDD>.md`) and prints
one summary line to stdout; excerpts never reach the terminal (FR-113, C-1). Exit codes:
0 success, 2 usage error (missing transcripts, existing output file, bad arguments).
The report contains personal and customer names: keep it under `out/`, never commit it.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import TextIO

from ..application.extract_candidates import ExtractCandidates
from ..domain.report import render_report
from ..infrastructure.claude_code_transcripts import (
    ClaudeCodeTranscriptSource,
    TranscriptsUnavailable,
)

DEFAULT_PROJECTS_DIR = Path("~/.claude/projects")
DEFAULT_OUT_DIR = Path("out")
EXIT_OK = 0
EXIT_USAGE = 2


def main(
    argv: Sequence[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    today: date | None = None,
) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    parser = argparse.ArgumentParser(
        prog="extract-candidates",
        description="Collect correction candidates from Claude Code transcripts into Markdown.",
    )
    parser.add_argument("--projects-dir", type=Path, default=DEFAULT_PROJECTS_DIR)
    parser.add_argument("--since", type=date.fromisoformat, help="first day to include, YYYY-MM-DD")
    parser.add_argument("--min-score", type=int, default=1)
    parser.add_argument(
        "--out", type=Path, help="report path; default out/candidates-<YYYYMMDD>.md"
    )
    args = parser.parse_args(argv)

    projects_dir = args.projects_dir.expanduser()
    day = today if today is not None else date.today()
    out_path = args.out if args.out is not None else DEFAULT_OUT_DIR / f"candidates-{day:%Y%m%d}.md"
    if out_path.exists():
        print(f"error: output file already exists, not overwriting: {out_path}", file=err)
        return EXIT_USAGE

    try:
        extraction = ExtractCandidates(ClaudeCodeTranscriptSource(projects_dir)).handle(
            since=args.since, min_score=args.min_score
        )
    except TranscriptsUnavailable as error:
        print(f"error: {error}", file=err)
        return EXIT_USAGE

    report = render_report(
        extraction.candidates,
        extraction.stats,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        projects_dir=str(projects_dir),
        since=args.since.isoformat() if args.since else None,
        min_score=args.min_score,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    stats = extraction.stats
    print(
        f"scanned {stats.files_scanned} file(s), {stats.human_turns} human turn(s), "
        f"{len(extraction.candidates)} candidate(s) → {out_path}",
        file=out,
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
