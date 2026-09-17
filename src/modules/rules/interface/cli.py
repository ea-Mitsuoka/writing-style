"""Rules interface — command-line entry point and composition root.

    python3 -m src.modules.rules.interface.cli [--vault PATH]

Validates the vault's writing rules and prints one finding per line as
`<vault-relative path>:<requirement code>:<message>` (FR-012). Exit codes: 0 no findings,
1 findings, 2 usage error (no vault path, not a directory, unexpected layout; FR-011).
The vault path comes from `--vault` or `$OBSIDIAN_VAULT_PATH`. Findings go to stdout so
another tool can consume them; the count summary goes to stderr.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO

from ..application.validate_rules import ValidateRules
from ..infrastructure.filesystem_rule_source import (
    RULE_GLOB,
    RULES_DIR,
    FilesystemRuleSource,
    VaultLayoutError,
)

VAULT_ENV = "OBSIDIAN_VAULT_PATH"
EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


def main(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    env = environ if environ is not None else os.environ

    parser = argparse.ArgumentParser(
        prog="rules-validate",
        description="Validate the vault's writing rules (30_memory/feedback/ja-*.md).",
    )
    parser.add_argument("--vault", help=f"vault root; defaults to ${VAULT_ENV}")
    args = parser.parse_args(argv)

    vault = args.vault or env.get(VAULT_ENV)
    if not vault:
        print(f"error: no vault path; pass --vault or set {VAULT_ENV}", file=err)
        return EXIT_USAGE
    root = Path(vault).expanduser()
    if not root.is_dir():
        print(f"error: vault path is not a directory: {root}", file=err)
        return EXIT_USAGE

    try:
        report = ValidateRules(FilesystemRuleSource(root)).handle()
    except VaultLayoutError as error:
        print(f"error: {error}", file=err)
        return EXIT_USAGE

    for finding in report.findings:
        print(f"{finding.path}:{finding.code}:{finding.message}", file=out)
    if report.checked == 0:
        print(f"no rule files found under {RULES_DIR.as_posix()} ({RULE_GLOB})", file=out)
    else:
        print(f"checked {report.checked} rule file(s), {len(report.findings)} finding(s)", file=err)
    return EXIT_FINDINGS if report.findings else EXIT_CLEAN


if __name__ == "__main__":
    raise SystemExit(main())
