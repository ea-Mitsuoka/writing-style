---
id: runbook-triage-correction-candidates
title: 候補の仕分けとルール化
severity: ticket
last-verified: 2026-09-19
---

# 候補の仕分けとルール化

**Trigger:** 月 1 回、または AI の日本語への指摘が溜まったと感じたとき（`docs/requirements/extraction.md` §9）。
**Impact if unhandled:** 指摘がルールにならず、同じ修正を毎セッション繰り返す。
**Safe to execute by agent:** 一部 — 手順 3 の判定提案と手順 5 のファイル作成は AI に任せられる。手順 4 の採否決定、手順 7 の Vault commit、手順 8 の削除は利用者が行う。

## この手順で得るもの

`make extract-candidates` が出した候補一覧から、日本語表現への指摘だけを選び、Vault
`ea-Mitsuoka/ai-memory` に表現ルール（`30_memory/feedback/ja-<kind>-<slug>.md`）として保存し、
書式検証を通した状態で commit する。

## 用語

この文書で使う語。用語集 [docs/glossary.md](../glossary.md) の定義に加え、次を使う。

| 語 | 意味 |
| -- | -- |
| 候補一覧 | `make extract-candidates` が書く 1 ファイル `out/candidates-<YYYYMMDD>.md`。候補をスコア順に並べ、各候補に発話本文（400 文字まで）と直前の assistant 本文（200 文字まで）を載せる。人名・案件名を含み得る |
| 下書き | AI がチャット応答として出す、`rule-atom` 雛形を埋めた表現ルールの案。ファイルではない。利用者が採否を決めるまでは Vault に書かない |
| `rule-atom` | Vault の雛形 `~/ai-memory/90_templates/rule-atom.md`。frontmatter（`kind` / `scope` / `updated`）、`## ルール`、`## NG / OK`、`**Why:**`、`**How to apply:**` の順で構成される。書式の規約は Vault `AGENTS.md` の「表現ルール」節 |
| ブリッジ | `~/.claude/CLAUDE.md` の `## Memory` ブロックが Vault のコア文脈を import する設定。手順の説明は Vault `00_system/claude-code-bridge.md`。本手順では必須ではない（手順 3 で読むファイルを明示するため） |

## 前提

- `~/Project/writing-style` と `~/ai-memory` が checkout 済みで、どちらも Python 3.11 以上が
  使える。追加の依存は無い。
- `OBSIDIAN_VAULT_PATH` が `~/ai-memory` を指している（`zsh -c 'echo $OBSIDIAN_VAULT_PATH'`
  で値が出る）。未設定でも手順 6 の `VAULT=` で代替できる。
- Claude Code のセッション記録が `~/.claude/projects/` にある。別の場所なら手順 2 で
  `PROJECTS_DIR=` を渡す。

## Steps

1. Vault を最新にする。

   ```bash
   cd ~/ai-memory && git pull && git status --short
   ```

   - Expect: `git status --short` が何も出さない。
   - If not: 未 commit の変更がある。先に commit するか退避してから進む。仕分けの途中で他の
     変更が混ざると、手順 7 の commit に無関係な差分が入る。

2. 候補一覧を作る。`SINCE=` には前回この手順を実施した日を入れる。初回は省略して全期間を対象にする。

   ```bash
   cd ~/Project/writing-style && make extract-candidates SINCE=2026-09-01
   ```

   - Expect: 標準出力に 1 行
     `scanned <N> file(s), <M> human turn(s), <K> candidate(s) → out/candidates-<YYYYMMDD>.md`
     が出て終了コード 0。抜粋は端末に出ない。
   - If not: `error: output file already exists, not overwriting: out/candidates-<YYYYMMDD>.md`
     なら同日に既に実行している。前回の一覧を使うか、`OUT=out/candidates-<YYYYMMDD>-2.md`
     を付けて再実行する。`error:` で記録ディレクトリが無い・`.jsonl` が 0 件と出たら
     `PROJECTS_DIR=<実際のパス>` を付ける。
   - 候補が多すぎる（目安 100 件超）ときは `MIN_SCORE=3` を付けて弱キーワードだけの候補を
     外す。スコアの規則は `docs/requirements/extraction.md` FR-106。

3. Claude Code のセッションで AI に判定を提案させる。writing-style のディレクトリで
   セッションを開き、次の指示を送る。`<YYYYMMDD>` は手順 2 の出力に置き換える。

   ```bash
   cd ~/Project/writing-style && claude
   ```

   送る指示文:

   > 次の 3 ファイルを読んで。`out/candidates-<YYYYMMDD>.md`、
   > `~/ai-memory/AGENTS.md` の「表現ルール」節、`~/ai-memory/90_templates/rule-atom.md`。
   > 候補一覧の各候補について、スコア順に「日本語表現への指摘」「指摘でない」「判断できない」
   > のいずれかと、判定理由を 1 行で表にして。
   > 「指摘」と判定したものは、同じ内容のものをまとめ、`rule-atom` の雛形を埋めた下書きを
   > チャットの応答として出して。ファイルは作らないで。
   > 下書きの `## NG / OK` は一覧の文をそのまま写さず、一般化した例にして。案件名・人名・
   > 顧客名・社名を含めないで。
   > 既存のルール `~/ai-memory/30_memory/feedback/ja-*.md` と重なるものは、新規の下書きでは
   > なく「既存ルール `<ファイル名>` に NG / OK 例を追加」として、追加する例だけを出して。

   - Expect: 判定表と、ルールごとの下書き（または既存ルールへの追加例）がチャットに出る。
     `git status --short` と `ls ~/ai-memory/30_memory/feedback` に変化がない。
   - If not: AI がファイルを作っていたら、内容を確認する前に削除させる（採否前の Vault 書き込みは
     §4.2 違反）。候補数が多くて応答が途中で切れるときは、「スコア 5 以上だけ」のように範囲を
     区切って複数回に分ける。

4. 下書きごとに採否を決める。判断の基準は 4 つで、1 つでも外れる下書きは不採用にするか
   直してから採用する。

   | 基準 | 確認すること |
   | -- | -- |
   | 自分の指摘か | 元の候補が、AI の日本語に対する自分の修正要求だった（作業指示・仕様変更ではない） |
   | `scope` が妥当か | ルールが効く文書種別だけが並んでいる。全部にしない |
   | 例が一般化されているか | `## NG / OK` に案件名・人名・顧客名・社名・固有のファイル名が無い |
   | 既存と重複しないか | `~/ai-memory/MEMORY.md` の `## feedback` 節に同じ趣旨のルールが無い。あれば既存ファイルの `## NG / OK` に例を追加し `updated` を今日にする |

   - Expect: 採用する下書きと、直す箇所が決まっている。
   - If not: 迷う下書きは不採用にする。同じ指摘が再発したときに改めて候補に出る（`AGENTS.md`
     「再発時の扱い」）。

5. 採用したルールを Vault に書く。AI に「採用した下書き `<ルール名>` を
   `~/ai-memory/30_memory/feedback/ja-<kind>-<slug>.md` に書き、`~/ai-memory/MEMORY.md` の
   `## feedback` 節に 1 行追記して」と指示するか、自分でファイルを作る。

   - Expect: 新しいファイルが `ls ~/ai-memory/30_memory/feedback` に出る。`MEMORY.md` の
     `## feedback` 節に `- [<title>](30_memory/feedback/ja-<kind>-<slug>.md) — <hook>` の行がある。
     frontmatter の `updated` は今日の日付。
   - If not: ファイル名が `ja-(term|style|structure)-[a-z0-9-]+.md` に一致しないと手順 6 で
     `FR-002` として検出される。先に直す。

6. 書式を検証する。

   ```bash
   cd ~/Project/writing-style && make rules-validate
   ```

   - Expect: 標準エラーに `checked <N> rule file(s), 0 finding(s)`、終了コード 0。
   - If not: 標準出力に `30_memory/feedback/ja-....md:FR-0xx:<メッセージ>` が 1 件 1 行で出て
     終了コード 1。`FR-0xx` の意味は `docs/requirements.md` §4 の表で引き、ファイルを直して
     再実行する。`error: no vault path; pass --vault or set OBSIDIAN_VAULT_PATH` と出て
     終了コード 2 なら `make rules-validate VAULT=~/ai-memory` で実行する。

7. Vault の整合性を検査して commit する。

   ```bash
   cd ~/ai-memory && python3 scripts/validate_vault.py && git add -A && git commit -m "feedback: 表現ルールを追加" && git push
   ```

   - Expect: `vault OK (<N> notes checked)` の後に commit と push が完了する。
   - If not: `validate_vault.py` が frontmatter 欠落・wikilink 切れ・索引漏れを報告する。
     手順 5 の追記漏れが主な原因なので、報告された箇所を直して再実行する。commit は
     検査が通るまで行わない（`&&` で連結しているため通らなければ止まる）。

8. 候補一覧を削除する。

   ```bash
   rm ~/Project/writing-style/out/candidates-*.md
   ```

   - Expect: `ls ~/Project/writing-style/out` が空。
   - If not: 削除を忘れても `out/` は `.gitignore` 済みで commit されない。ただし共有・
     バックアップ経路に載る可能性があるため、この手順の完了条件に含める。

## Verification

- `cd ~/Project/writing-style && make rules-validate` が `0 finding(s)` で終了コード 0。
- `cd ~/ai-memory && git status --short` が何も出さず、`git log -1` が手順 7 の commit。
- `~/Project/writing-style/out/` に `candidates-*.md` が無い。
- 次のセッションで、追加したルールの `scope` に該当する文章を AI に書かせ、同じ指摘が
  再発しない。再発したら `AGENTS.md`「再発時の扱い」に従い `## NG / OK` に例を追加する。

## 継続的な運用（手順の外で毎回行うこと）

AI の日本語を直す発話には `#表現` を含める。

> #表現 「〇〇」は硬い。「△△」にして。

このタグは FR-106 で 10 点（強キーワードは種類ごとに 3 点）のため、次回の候補一覧で上位に
並ぶ。タグが無くても「わかりづらい」「不自然」などの強キーワードがあれば候補にはなるが、
キーワードを含まない指摘は拾えない（`docs/requirements/extraction.md` R-3）。

## Escalation

| 状況 | 行き先 |
| -- | -- |
| 自分が覚えている指摘が候補一覧に無い | 未解決事項 Q-101（キーワード集合の見直し）。当該発話の語句を issue #8 に書く |
| ハーネスの自動生成文や重複した発話が候補に混ざる | issue #12 |
| 書式検証の要件そのものを変えたい | `docs/requirements.md` §4 の変更として PR |
