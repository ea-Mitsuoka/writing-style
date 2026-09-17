---
id: project-adr-index
title: プロジェクト ADR 索引
---

# プロジェクト Architecture Decision Records（ADR）

このリポジトリ固有の決定。継承した基盤の決定は [docs/foundation/adr/](../foundation/adr/README.md)
にある。手順・状態遷移・雛形は基盤の ADR 索引と `.skills/architecture.skill.md` に従い、
本文は日本語で書く（ADR-0005）。

## 索引

| # | 題名 | 範囲 | 状態 | 日付 |
| -- | -- | -- | -- | -- |
| [0001](0001-validate-writing-rules-from-the-memory-vault.md) | 表現ルールの検証を、Vault を読む独立モジュールとして実装する | rules モジュール、Vault との境界、CI の検証範囲 | accepted | 2026-09-18 |
| [0002](0002-extract-correction-candidates-from-claude-code-transcripts.md) | 指摘候補の抽出を、記録を読むだけの独立モジュールと人の仕分けで行う | extraction モジュール、セッション記録との境界、機密の扱い | proposed | 2026-09-18 |
