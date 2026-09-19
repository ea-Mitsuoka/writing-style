# writing-style

<!-- repository-readme-owner: ea-Mitsuoka/writing-style -->

日本語表現ルールの**改善ループを回す仕組み**を置くリポジトリ。AI が書いた日本語への指摘
（用語の揺れ・不自然な言い回し・過剰な敬語など）を、再発防止のルールとして蓄積・検証・
配布するためのスクリプトと運用手順を管理する。

> **AI agents:** stop reading this file. Your entry point is [CLAUDE.md](CLAUDE.md)
> (Claude Code) or [AGENTS.md](AGENTS.md) (everyone else).

## このリポジトリが持つもの・持たないもの

| 区分 | 内容 | 置き場所 |
| -- | -- | -- |
| **持つ** | 抽出（指摘の回収）・正規化（ルール化）・検証（書式と適用範囲の必須項目）・昇格（安定したルールを共通 AI 基盤の Skill に変換）を行うスクリプトと手順 | このリポジトリ |
| **持たない** | ルール本文（用語対訳表・文体規則・構造規則・NG/OK 例） | メモリ Vault [ai-memory](https://github.com/ea-Mitsuoka/ai-memory) の `30_memory/feedback/` |
| **持たない** | 開発方針（コード規約・レビュー・ワークフロー） | [ai-dev-foundation](https://github.com/ea-Mitsuoka/ai-dev-foundation) の `.ai/` |

ルール本文をここに置かない理由は、ルールが**人の記憶**（AI 全般に読ませる文脈）であって、
特定リポジトリの成果物ではないため。Vault は各 AI セッションが起動時に読む正典であり、
`updated` の日付が「安定性」の判断材料になる。このリポジトリはその正典を**読んで処理する側**。

## 改善ループ

```
抽出 ──▶ ルール化 ──▶ 保存（Vault） ──▶ 検証 ──▶ 昇格（Skill）
  ▲                                       │
  └────────── 再発したら具体例を追加 ◀──────┘
```

| 段階 | 内容 | 担当 |
| -- | -- | -- |
| 抽出 | Claude Code のセッション記録や claude.ai のエクスポートから、表現への指摘を回収する | スクリプト（この repo） |
| ルール化 | 用語固定・文体規則・構造規則の 3 種に正規化し、**適用範囲**と **NG/OK 例**を必須とする | 人 + AI |
| 保存 | `30_memory/feedback/` に 1 ルール 1 ファイルで置き、`MEMORY.md` に索引する | Vault の規約に従う |
| 検証 | 同種の文章生成で同じ指摘が再発しないかを見る。再発したら具体例を追加 | 人 |
| 昇格 | 直近 2〜3 か月、追記も修正もないルールだけを Skill に変換する | スクリプト（この repo） |

更新は **Vault → 配布先（Skill / 他ツールのメモリ）の一方向**に固定する。逆流させない。

## 状態

| 段階 | 状態 |
| -- | -- |
| ルールファイルの書式（frontmatter の `kind` / `scope`、本文の順序） | 定義済み。Vault の `AGENTS.md`「表現ルール」節と `rule-atom` 雛形 |
| 書式検証（`src/modules/rules`、[ADR-0001](docs/adr/0001-validate-writing-rules-from-the-memory-vault.md)） | 実装済み。`make rules-validate`（`$OBSIDIAN_VAULT_PATH` または `VAULT=<path>`）で実 Vault を検査する。要件は [docs/requirements.md](docs/requirements.md) |
| Claude Code セッション記録からの指摘抽出（`src/modules/extraction`、[ADR-0002](docs/adr/0002-extract-correction-candidates-from-claude-code-transcripts.md)） | 実装済み。`make extract-candidates`（`SINCE=` / `MIN_SCORE=` / `OUT=` / `PROJECTS_DIR=`）が候補一覧を `out/` に書く。**一覧は人名・案件名を含むため commit しない。** 候補から表現ルールを作る手順書は [docs/runbook/update-writing-rules.md](docs/runbook/update-writing-rules.md) |
| 安定判定と Skill への昇格 | 未着手（別 issue で要件化） |

検証の出力は 1 件 1 行 `相対パス:要件コード:メッセージ`（終了コード 0 = 違反なし、1 = 違反あり、
2 = 使い方の誤り）。CI は同梱 fixture に対するテストのみ実行し、実 Vault の検証はローカルで行う。

## 基盤

[ai-dev-foundation](https://github.com/ea-Mitsuoka/ai-dev-foundation) から生成。規約・ガードレール・
CI・スキルは `.ai/` と `.claude/` に継承されている。継承関係は
`.github/inheritance/` に記録し、親の更新は Template Sync の PR として届く。
