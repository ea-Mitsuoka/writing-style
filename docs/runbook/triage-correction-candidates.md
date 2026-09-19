---
id: runbook-triage-correction-candidates
title: 候補の仕分けとルール化
severity: ticket
---

# 候補の仕分けとルール化

`make extract-candidates` が出した候補一覧から日本語表現への指摘を選び、Vault に表現ルールとして
保存するまでの手順。月 1 回、または指摘が溜まったときに行う。放置すると同じ修正を毎セッション
繰り返す。

| # | 手順 | 行う者 |
| -- | -- | -- |
| 1 | 候補一覧を作る | 利用者 |
| 2 | AI に判定と下書きを出させる | AI |
| 3 | 下書きの採否を決める | 利用者 |
| 4 | 採用分を Vault に書く | AI または利用者 |
| 5 | 書式を検証して commit する | 利用者 |
| 6 | 候補一覧を削除する | 利用者 |

パスは、このリポジトリが `~/Project/writing-style`、Vault が `~/ai-memory` にある前提で書く。

検証状況（2026-09-19）: 手順 1・5・6 はコマンドと出力を実行して確認した。手順 2〜4 は通しで
未実施。最初の仕分けで確認し、通ったら frontmatter に `last-verified` を入れる。

## 手順

### 1. 候補一覧を作る

```bash
cd ~/ai-memory && git pull && git status --short
cd ~/Project/writing-style && make extract-candidates SINCE=<前回の実施日>
```

1 行目で Vault に未 commit の変更が無いことを確かめる（あれば先に片付ける）。2 行目が
`scanned … candidate(s) → out/candidates-<日付>.md` を出せば成功。初回は `SINCE=` を省く。
候補が 100 件を超えるときは `MIN_SCORE=3` を付け、弱いキーワードだけの候補を外す。

| 出力 | 対処 |
| -- | -- |
| `error: output file already exists` | 同日に実行済み。既存の一覧を使うか `OUT=out/candidates-<日付>-2.md` を付ける |
| 記録が無い旨の `error:` | `PROJECTS_DIR=<記録の場所>` を付ける。既定は `~/.claude/projects` |

### 2. AI に判定と下書きを出させる

このリポジトリのディレクトリで Claude Code を開き、次を送る。

> `out/candidates-<日付>.md`、`~/ai-memory/AGENTS.md` の「表現ルール」節、
> `~/ai-memory/90_templates/rule-atom.md` を読んで。
> 各候補をスコア順に「指摘」「指摘でない」「判断できない」に分け、理由を 1 行で表にして。
> 「指摘」は同じ内容をまとめ、`rule-atom` の雛形を埋めた下書きをチャットに出して。ファイルは作らないで。
> `## NG / OK` は一覧の文を写さず一般化し、案件名・人名・顧客名・社名を入れないで。
> 既存の `~/ai-memory/30_memory/feedback/ja-*.md` と重なるものは新規にせず、
> 「既存ルール `<ファイル名>` に例を追加」として追加分だけ出して。

判定表と下書き（ルール案）がチャットに出る。この時点で Vault にファイルが増えていたら消させる。
採否が決まる前に Vault へ書かないのが業務ルール。応答が途中で切れるときは「スコア 5 以上だけ」の
ように範囲を区切り、複数回に分ける。

### 3. 下書きの採否を決める

下書きごとに次を確かめ、1 つでも外れたら直すか不採用にする。迷うものは不採用でよい。再発すれば
次回また候補に出る。

- 元の候補が、AI の日本語に対する自分の修正要求である。作業指示や仕様変更ではない
- `scope` が、そのルールの効く文書種別だけになっている
- `## NG / OK` に案件名・人名・顧客名・社名が無い
- `~/ai-memory/MEMORY.md` の `## feedback` に同じ趣旨のルールが無い。あれば新規にせず、
  既存ファイルの `## NG / OK` に例を追加して `updated` を更新する

### 4. 採用分を Vault に書く

AI に次を指示するか、自分で書く。

> 採用した下書き `<ルール名>` を `~/ai-memory/30_memory/feedback/ja-<kind>-<slug>.md` に書き、
> `~/ai-memory/MEMORY.md` の `## feedback` に 1 行追記して。

ファイル名は `ja-(term|style|structure)-<英小文字とハイフン>.md`。書式は雛形
`~/ai-memory/90_templates/rule-atom.md` に従い、`updated` は今日の日付にする。`MEMORY.md` に足す
行は `- [<title>](30_memory/feedback/<ファイル名>) — <一行の要約>`。

「既存ルールに例を追加」の下書きは、新規ファイルを作らず、そのファイルの `## NG / OK` に行を
追加して `updated` を今日にする。`MEMORY.md` は変えない。

### 5. 書式を検証して commit する

```bash
cd ~/Project/writing-style && make rules-validate
cd ~/ai-memory && python3 scripts/validate_vault.py && git add -A && git commit -m "feedback: 表現ルールを追加" && git push
```

1 行目が `checked <N> rule file(s), 0 finding(s)`、2 行目が `vault OK` の後に push まで進めば完了。

| 出力 | 対処 |
| -- | -- |
| `<ファイル>:FR-0xx:<メッセージ>`（終了コード 1） | 書式違反。コードの意味は [docs/requirements.md](../requirements.md) §4。直して再実行 |
| `error: no vault path`（終了コード 2） | `OBSIDIAN_VAULT_PATH` が未設定。`make rules-validate VAULT=~/ai-memory` で実行 |
| `validate_vault.py` が索引漏れ・wikilink 切れを報告 | 手順 4 の `MEMORY.md` 追記を直す。`&&` で繋いでいるため commit はされていない |

### 6. 候補一覧を削除する

```bash
rm ~/Project/writing-style/out/candidates-*.md
```

候補一覧は人名・案件名を含む。`out/` は gitignore 済みだが、共有やバックアップに載せないため
削除して終える。

## 終わったことの確認

- `make rules-validate` が `0 finding(s)`、Vault の `git status --short` が空、`out/` に候補一覧が無い。
- 次のセッションで該当 `scope` の文章を書かせ、同じ指摘が出ない。出たら `## NG / OK` に例を追加する。

## 日常の習慣

AI の日本語を直す発話に `#表現` を付ける。次回の候補一覧で最上位に並ぶ。キーワードを含まない
指摘は拾えない。

## うまくいかないとき

| 状況 | 行き先 |
| -- | -- |
| 覚えている指摘が候補一覧に無い | issue #8（キーワードの見直し）に当該発話の語句を書く |
| 自動生成文や重複した発話が候補に混ざる | issue #12 |

## 関連

- 役割分担と業務ルール: [docs/requirements/extraction.md](../requirements/extraction.md) §4.1・§4.2
- 用語（候補・候補一覧・仕分け）: [docs/glossary.md](../glossary.md)
- 表現ルールの規約: Vault `AGENTS.md` の「表現ルール」節
