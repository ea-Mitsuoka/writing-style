---
id: module-rules
title: Rules Module
updated: 2026-09-18
---

# Rules Module

Purpose: validate the writing rules (`ja-<kind>-<slug>.md`) stored in the memory vault
`ea-Mitsuoka/ai-memory` against the format its `AGENTS.md`「表現ルール」section defines,
and report every violation with the requirement id it breaks. The module reads rule
documents through a port and never writes to the vault. It does **not** own rule
content, stability judgement, or promotion to skills (ADR-0001).

## Public API (the contract — everything else in this module is private)

| Entry point | Layer | Description |
| -- | -- | -- |
| `validate_rule(path, text) -> tuple[Finding, ...]` | domain | Check one document; one finding per violated requirement, or a single `FR-013` when the frontmatter cannot be parsed |
| `ValidateRules(source).handle() -> Report` | application | Validate every document a `RuleSource` yields; `Report.findings` in source order, `Report.checked` documents counted |
| `RuleSource` / `RuleDocument` | application | Port a source adapter implements; a document is `(path, text)` or `(path, None, read_error)` |
| `SCOPE_TAGS`, `KINDS` | domain | The vocabulary copied once from the vault `AGENTS.md`; the only place it exists in code |
| `FilesystemRuleSource(vault_root)` | infrastructure | `RuleSource` over a vault checkout: `30_memory/feedback/ja-*.md` directly under it (FR-001), sorted by name; raises `VaultLayoutError` when the directory is absent |
| `main(argv, environ, stdout, stderr) -> int` | interface | CLI (`python3 -m src.modules.rules.interface.cli`, `make rules-validate`): `--vault` or `$OBSIDIAN_VAULT_PATH`; one finding per stdout line as `path:code:message`; exit 0 clean, 1 findings, 2 usage error (FR-011, FR-012) |

## Events

| Direction | Event | Schema | Notes |
| -- | -- | -- | -- |
| — | — | — | none |

## Owned data

None. Rule documents belong to the vault; this module holds no state between runs.

## Invariants (MUST always hold — each maps to a test)

1. A document that matches the vault prototype rule produces no findings.
2. `Finding.code` is a requirement id from `docs/requirements.md` (`FR-002` … `FR-013`),
   and each violated requirement is reported once per document.
3. A document whose frontmatter cannot be parsed, or that could not be read, produces
   exactly one finding (`FR-013`) and no others.
4. `SCOPE_TAGS` equals the six tags listed in the vault `AGENTS.md` (2026-09-18).
5. The module performs no write to any source it reads.

## Dependencies

| Uses module | Via | Why |
| -- | -- | -- |
| — | — | none; `domain/` and `application/` import only the standard library (ARC-002) |

## Layout

```
domain/frontmatter.py     # frontmatter block parser (flat keys + one nested `metadata:` level)
domain/rule.py            # Finding, KINDS, SCOPE_TAGS, validate_rule
application/ports.py      # RuleSource (port), RuleDocument
application/validate_rules.py  # ValidateRules use case, Report
infrastructure/filesystem_rule_source.py  # FilesystemRuleSource (adapter), VaultLayoutError
interface/cli.py          # main(): argument parsing, wiring, output format, exit codes
```

Tests mirror this tree: `tests/modules/rules/unit/` (domain, application; no I/O) and
`tests/modules/rules/integration/` (filesystem adapter and CLI over temporary vaults).
