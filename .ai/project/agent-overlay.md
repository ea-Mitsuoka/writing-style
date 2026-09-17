---
id: writing-style-agent-overlay
title: Writing Style Repository Facts
authority: 3
read_when: [agent-entry]
---

# Writing Style Repository Facts

This protected project layer contains repository identity and stack facts only. The
explicit agent profile loads it after the inherited foundation contract.

- Repository: `ea-Mitsuoka/writing-style`.
- Role: tooling for the Japanese writing-style improvement loop — extraction of
  wording corrections, normalization into rules, validation of rule files, and
  promotion of stable rules to shared AI skills.
- Rule storage: rule content is not stored in this repository. The canonical rules
  live in the private memory vault `ea-Mitsuoka/ai-memory` under `30_memory/feedback/`
  and are indexed by its `MEMORY.md`. This repository reads and processes them.
- Stack: Python 3.11+ standard-library scripts. No application runtime, database, or
  deployment target.
- Execution model: local CLI and GitHub Actions. Scripts read Markdown rule files and
  emit validation reports or skill files. Writing to the vault is a separate reviewed
  operation in that repository.
- Language: project-owned documents under `docs/` and the root README are Japanese
  (ADR-0005); `.ai/` and agent-facing files remain English (ADR-0002).
