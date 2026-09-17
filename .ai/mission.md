---
id: mission
title: Mission
authority: 4
read_when: [onboarding, planning, architecture]
---

# Mission

## What this project is

writing-style — tooling for the Japanese writing-style improvement loop: it extracts
wording corrections from AI sessions, normalizes them into scoped rules, validates rule
files, and promotes stable rules to shared AI skills.

| Field | Value |
|-------|-------|
| Problem being solved | Corrections to AI-written Japanese (terminology drift, unnatural phrasing, excessive honorifics) recur across sessions because they are not captured as rules with an explicit scope and NG/OK examples. |
| Primary users | The repository owner, and the AI agents that draft Japanese text for them (Claude Code, claude.ai, other tools that read the memory vault). |
| Core value | One extraction → normalization → storage → validation → promotion loop with a single canonical rule store; a correction made once stops recurring. |
| Explicitly out of scope | Storing rule content here — the canonical rules live in the `ea-Mitsuoka/ai-memory` vault under `30_memory/feedback/`. General development policy — owned by `ea-Mitsuoka/ai-dev-foundation`. Any chat UI or hosted service. |

## Success criteria

1. A rule file that lacks an applicability scope, an NG/OK example pair, or carries a
   source reference (case or customer name) fails validation in CI and locally.
2. Each rule records the sessions in which it was cited; a rule whose correction recurs
   after it was added is flagged for a concrete-example revision instead of silently
   accumulating duplicates.
3. Promotion to a skill is possible only for rules whose `updated` date is older than
   the configured stability window (default 60 days) and that pass criterion 1.

## Role of AI agents in this project

AI agents are long-term team members, not code generators. Expectations:

- **Own the full task lifecycle**: requirements clarification → design → implementation →
  tests → documentation → PR. A task is not done when code compiles; it is done when the
  Definition of Done in `workflow.md` (WF-090) is met.
- **Preserve intent**: when code and documentation disagree, investigate which is correct
  before changing either. Record the resolution.
- **Prefer reversible steps**: small PRs, feature flags, additive migrations.
- **Escalate, don't guess**: for the triggers in the loaded
  [foundation agent contract](contracts/foundation/agent-entry.md#escalation), stop and
  ask the human. For everything else, decide and record the reasoning.

## Human role

Humans own: product direction, priority calls, ADR approval, release approval,
security-sensitive decisions. AI prepares options and recommendations; humans decide.
