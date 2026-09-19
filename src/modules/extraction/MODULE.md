---
id: module-extraction
title: Extraction Module
updated: 2026-09-18
---

# Extraction Module

Purpose: collect **candidates** for the owner's corrections of AI-written Japanese from
Claude Code session transcripts (`~/.claude/projects/**/*.jsonl`), score them by keyword
weighting, and render a Markdown list for human and AI triage. It reads only; it does
**not** decide what is a correction, write rules, or touch the vault (ADR-0002).

## Public API (the contract — everything else in this module is private)

| Entry point | Layer | Description |
| -- | -- | -- |
| `score_turn(turn) -> Candidate \| None` | domain | Score one `HumanTurn` per FR-106; None when not Japanese or score 0 |
| `rank(candidates) -> tuple[Candidate, ...]` | domain | Score descending, timestamp descending, undated last (FR-107) |
| `deduplicate(candidates) -> tuple[Candidate, ...]` | domain | Merge candidates sharing text and timestamp, keep the first, record the other sessions in `Candidate.duplicate_sessions` (FR-114) |
| `render_report(candidates, stats, *, generated_at, projects_dir, since, min_score) -> str` | domain | Markdown per FR-110 (400 / 200-character excerpts) |
| `ExtractCandidates(source).handle(since, min_score) -> Extraction` | application | Scan through a `TranscriptSource`, score, filter, deduplicate, rank; returns candidates and `ScanStats` |
| `TranscriptSource` / `ScanResult` | application | Port an adapter implements: format-neutral `HumanTurn`s plus statistics |
| `TAG`, `STRONG_KEYWORDS`, `WEAK_KEYWORDS` and their scores | domain | The vocabulary and weights, copied once from `docs/requirements/extraction.md` FR-106 |

## Events

| Direction | Event | Schema | Notes |
| -- | -- | -- | -- |
| — | — | — | none |

## Owned data

None. Transcripts belong to Claude Code; the candidate report belongs to the owner under
`out/` and is never committed.

## Invariants (MUST always hold — each maps to a test)

1. A turn without Japanese, with score 0, or beginning with the harness continuation
   summary, is never a candidate.
2. Each keyword kind counts once per turn; weak keywords count only when the turn is at
   most 200 characters.
3. Ranking is total and deterministic: score desc, then timestamp desc, undated last.
   Candidates sharing text and timestamp appear once, keeping the first one scanned.
4. The rendered report is a pure function of its inputs (same input, same text).
5. `domain/` and `application/` import only the standard library and never the `rules`
   module.

## Dependencies

| Uses module | Via | Why |
| -- | -- | -- |
| — | — | none (ADR-0002: independent of `rules`) |

## Layout

```
domain/candidate.py       # HumanTurn, Candidate, ScanStats, keyword weights, score_turn, rank
domain/report.py          # render_report (Markdown)
application/ports.py      # TranscriptSource (port), ScanResult
application/extract_candidates.py  # ExtractCandidates use case, Extraction
infrastructure/claude_code_records.py      # human_text / assistant_text / record_timestamp (record shape lives here only)
infrastructure/claude_code_transcripts.py  # ClaudeCodeTranscriptSource (adapter), TranscriptsUnavailable
interface/cli.py          # main(): arguments, wiring, report file, summary line, exit codes
```

Adapter and CLI contract: `ClaudeCodeTranscriptSource(projects_dir).scan(since)` walks
`**/*.jsonl` in sorted order, treats the first path component as the project and the file
stem as the session id, pairs each human turn with the preceding assistant text in the same
file, keeps undated records under `--since`, and raises `TranscriptsUnavailable` when the
directory is missing or empty. `main(argv, stdout, stderr, today)` writes the report to
`--out` (default `out/candidates-<YYYYMMDD>.md`, never overwriting), prints one summary
line, and exits 0 or 2. Tests mirror this tree: `tests/modules/extraction/unit/` (domain,
application, record interpretation; no I/O) and `tests/modules/extraction/integration/`
(transcript adapter and CLI over temporary directories).
