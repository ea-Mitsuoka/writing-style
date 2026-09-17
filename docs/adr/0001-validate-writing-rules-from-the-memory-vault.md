---
id: adr-0001
title: ADR-0001 — 表現ルールの検証を、Vault を読む独立モジュールとして実装する
status: proposed
updated: 2026-09-18
---

# ADR-0001: 表現ルールの検証を、Vault を読む独立モジュールとして実装する

| Field | Value |
| -- | -- |
| Status | proposed |
| Date | 2026-09-18 |
| Deciders | リポジトリ所有者 |
| Author | Claude Fable 5.1（AI agent） |
| Supersedes / Superseded by | — |

## Context

日本語表現ルールの本文は、このリポジトリではなくメモリ Vault `ea-Mitsuoka/ai-memory` の
`30_memory/feedback/ja-<kind>-<slug>.md` に置く（`.ai/decision-log.md` LOG-0050）。Vault 側の
`AGENTS.md`「表現ルール」節（2026-09-18）が書式を定めている: frontmatter に `metadata.kind`
（`term` / `style` / `structure`）と `metadata.scope`（定義済みタグの 1 つ以上）を持ち、本文は
`## ルール` → `## NG / OK`（例の対を 1 組以上）→ `**Why:**` / `**How to apply:**` の順で書く。

Vault の CI（`scripts/validate_vault.py`）が検査するのは共通 frontmatter（`name` /
`description` / `type` / `updated`）、wikilink、索引の整合だけで、表現ルール固有の項目は
検査しない。書式違反、特に**適用範囲の欠落**は、ルールを別の文脈へ誤適用する事故につながる
ため、機械検証が必要である。

制約は次のとおり。

- Vault は Private リポジトリで、このリポジトリの CI からは読めない。
- Vault の仕組みは `ai-memory-template` から継承しており、テンプレート側はベンダー中立・
  用途非依存を保つ方針である。
- このリポジトリは標準ライブラリのみで動く（`.ai/architecture.md`）。
- 新しいモジュールは `src/modules/<context>/` の 4 層構成に従う（ARC-001）。

## Options considered

### Option 1: 何もしない（人のレビューに任せる）

保存時に人が書式を確認する。実装コストはないが、確認漏れがそのまま誤適用につながり、
ルール件数が増えるほど確認が形骸化する。元の運用方針が「範囲のないルールは誤適用を招く」と
明記している以上、機械的な歯止めがないのは要件を満たさない。

### Option 2: Vault のテンプレート `validate_vault.py` に検査を追加する

`ai-memory-template` の検証スクリプトに `ja-*` 固有の検査を足す。Vault の CI で直接動く利点が
あるが、テンプレートに特定用途（日本語表現ルール）の知識が入り、用途非依存の方針に反する。
また、検査ロジックの試用・修正が頻発する初期段階で、テンプレート → 各 Vault への同期を伴う
のは重い。

### Option 3: このリポジトリに検証モジュールを置き、Vault をポート経由で読む（採用）

`src/modules/rules/` に 4 層のモジュールを実装する。`domain` が書式の規則、`application` が
検証ユースケースと「ルールの供給源」ポート、`infrastructure` がファイルシステムのアダプタ、
`interface` が CLI。Vault の場所は `--vault` または `$OBSIDIAN_VAULT_PATH` で受け取る。

利点: 仕組みと本文の分離（LOG-0050）と一致する。テンプレートを汚さない。検査ロジックの
変更がこのリポジトリの PR で完結する。欠点: Vault の CI では動かず、実 Vault の検証は
ローカル実行になる（Follow-ups 参照）。

### Option 4: Vault の CI からこのリポジトリの検証を呼び出す

Vault 側の workflow がこのリポジトリを checkout して検証を走らせる。Option 3 の欠点を補うが、
リポジトリ間の依存とトークン設計が必要で、検証ロジックが安定していない段階では早い。
Option 3 の上に後から載せられるため、今回は採らない。

## Decision

Option 3 を採用する。

- 検証モジュールは `src/modules/rules/` に置き、`interface → application → domain` と
  `infrastructure → application → domain` の依存方向を守る（ARC-002）。
- 検査対象は **構造**に限る: 命名と `name` の一致、`type` / `kind` / `scope` / `updated` の
  値、見出しの順序、NG / OK 対の有無、`Why` / `How to apply` の有無。案件名・顧客名の混入は
  誤検知が多いため機械検証せず、人のレビュー事項とする。
- `scope` タグの語彙は Vault `AGENTS.md` が正典で、コードはそれを写した定数を 1 か所に持ち、
  出典を注記する。語彙が変わったら両方を同じ変更で更新する。
- モジュールは Vault に**書き込まない**。読み取りと報告のみ。
- CI は同梱の fixture に対する単体テストだけを実行する。実 Vault の検証は `make` ターゲット
  でローカル実行する。

## Consequences

**Positive:** 表現ルールの書式違反が保存前に機械的に検出できる。仕組み（このリポジトリ）と
本文（Vault）の分離が保たれ、テンプレートは用途非依存のまま。検査ロジックの変更が 1 リポジトリ
の PR で完結する。

**Negative:** 実 Vault の検証は人がローカルで実行する必要があり、忘れると違反が Vault に
入る。`scope` の語彙が Vault `AGENTS.md` とコードの 2 か所に存在し、片方だけの更新で乖離する
危険がある。

**Follow-ups:**

- Vault の CI からこの検証を呼ぶ手段（Option 4）を、検査ロジックが安定した後に別 issue で
  検討する。
- 安定判定（`updated` からの経過日数）と Skill への昇格は別 issue で扱う（issue #3 の対象外）。
- `docs/requirements.md` に要件、`docs/glossary.md` に用語を記録する（DOC-030）。
