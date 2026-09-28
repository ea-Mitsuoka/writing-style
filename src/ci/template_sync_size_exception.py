#!/usr/bin/env python3
"""Downgrade a GR-020 hard-limit failure for an authenticated Template Sync PR.

The inherited `scripts/pr_size_policy.py` measures the pull request and reports GR-025
checkpoints. It has no notion of Template Sync, whose PR carries the whole accepted parent
range and cannot be split. This gate receives that policy's exit status and turns only the
hard-limit failure (status 1) into a warning, and only for a same-repository sync PR opened
by the workflow bot with exact direct-parent provenance. Every other status passes through.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

TARGET_REPOSITORY = "ea-Mitsuoka/writing-style"
DIRECT_PARENT_REPOSITORY = "ea-Mitsuoka/ai-dev-foundation"
TEMPLATE_SYNC_BRANCH = re.compile(r"chore/template_sync_[0-9a-f]{7,40}\Z")
DIRECT_PARENT_SOURCE = re.compile(
    rf"^Direct-parent-source: https://github\.com/{re.escape(DIRECT_PARENT_REPOSITORY)}"
    r"@[0-9a-f]{40}$",
    re.MULTILINE,
)
HARD_LIMIT_STATUS = 1


def is_authenticated_template_sync(
    *,
    pr_author: str,
    head_repository: str,
    target_repository: str,
    head_ref: str,
    base_ref: str,
    pr_body: str,
) -> bool:
    """Return true only for a same-repository sync with exact parent provenance."""
    return all(
        (
            pr_author == "github-actions[bot]",
            target_repository == TARGET_REPOSITORY,
            head_repository == target_repository,
            TEMPLATE_SYNC_BRANCH.fullmatch(head_ref) is not None,
            base_ref == "main",
            DIRECT_PARENT_SOURCE.search(pr_body) is not None,
        )
    )


def gate(policy_status: int, *, authenticated_template_sync: bool) -> int:
    """Return the exit status the size step reports."""
    if policy_status == HARD_LIMIT_STATUS and authenticated_template_sync:
        print(
            "::warning::Authenticated mechanical Template Sync exceeds the numeric "
            "GR-020 limit; human review and every other required check remain mandatory."
        )
        return 0
    return policy_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy-status", required=True, type=int)
    parser.add_argument("--pr-author", required=True)
    parser.add_argument("--head-repository", required=True)
    parser.add_argument("--target-repository", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--pr-body-file", required=True, type=Path)
    args = parser.parse_args()
    try:
        pr_body = args.pr_body_file.read_text(encoding="utf-8")
    except OSError as error:
        print(f"::error::Invalid Template Sync size-exception input: {error}")
        return 2
    authenticated = is_authenticated_template_sync(
        pr_author=args.pr_author,
        head_repository=args.head_repository,
        target_repository=args.target_repository,
        head_ref=args.head_ref,
        base_ref=args.base_ref,
        pr_body=pr_body,
    )
    return gate(args.policy_status, authenticated_template_sync=authenticated)


if __name__ == "__main__":
    raise SystemExit(main())
