"""Test builders for writing-rule documents.

`prototype_rule()` reproduces the vault's first rule (`ja-term-gc-iam-roles.md`,
2026-09-18) so the conforming case has an expected value independent of the
implementation (TST-010, AC-2). `rule_text()` produces variants from named parts so a
test reads without opening other files.
"""

from __future__ import annotations

PROTOTYPE_PATH = "30_memory/feedback/ja-term-gc-iam-roles.md"

PROTOTYPE_FRONTMATTER = {
    "name": "ja-term-gc-iam-roles",
    "description": (
        "Google Cloud IAM の基本ロールは公式の日本語表示名で書き、ロール ID を併記する"
        "（roles/browser は「ブラウザ」、「閲覧者」は roles/viewer）"
    ),
    "type": "feedback",
    "kind": "term",
    "scope": "[customer-doc, decision-doc, internal-doc, slide]",
    "updated": "2026-09-18",
}

RULE_SECTION = """## ルール

Google Cloud IAM のロールを日本語文書で書くときは、**Google Cloud コンソールの日本語表示名**を
使い、初出時にロール ID を括弧で併記する。意味から訳し直さない。

| ロール ID | 書く | 書かない |
|-----------|------|---------|
| `roles/browser` | ブラウザ | 閲覧者、参照者、ブラウザー |
| `roles/viewer` | 閲覧者 | ビューア、参照者 |
"""

NG_OK_SECTION = """## NG / OK

| NG | OK |
|----|----|
| 閲覧者ロール（roles/browser）を付与 | ブラウザロール（`roles/browser`）を付与 |
"""

WHY_HOW_SECTION = """**Why:** 顧客・決裁者はコンソールの表示名で画面を見ている。

**How to apply:** IAM 設計書でロール名を書くとき、表示名 + ロール ID の形にする。
"""


def frontmatter_text(**overrides: str | None) -> str:
    """Render the frontmatter block. A value of None omits that key."""
    fields = {**PROTOTYPE_FRONTMATTER, **overrides}
    lines = ["---"]
    if fields["name"] is not None:
        lines.append(f"name: {fields['name']}")
    if fields["description"] is not None:
        lines.append(f"description: {fields['description']}")
    lines.append("metadata:")
    for key in ("type", "kind", "scope"):
        if fields[key] is not None:
            lines.append(f"  {key}: {fields[key]}")
    if fields["updated"] is not None:
        lines.append(f"updated: {fields['updated']}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def rule_text(
    *,
    frontmatter: str | None = None,
    rule: str = RULE_SECTION,
    ng_ok: str = NG_OK_SECTION,
    why_how: str = WHY_HOW_SECTION,
    **frontmatter_overrides: str | None,
) -> str:
    header = frontmatter if frontmatter is not None else frontmatter_text(**frontmatter_overrides)
    return "\n".join(part for part in (header, rule, ng_ok, why_how) if part)


def prototype_rule() -> str:
    return rule_text()
