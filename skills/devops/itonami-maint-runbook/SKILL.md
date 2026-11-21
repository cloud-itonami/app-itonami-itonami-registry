---
name: itonami-maint-runbook
description: Run the itonami-maint maturity iteration in wt-msloop.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-giemon/tree/0eb965a7e36385b4a4d967e027a89367e490c656
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-maint cron 実行手順

## 環境の重要事実 (falsify-56 で判明、毎反復頭に確認)

1. **正本 ledger は CWD の `worktree/` ではない**。`~/.hermes/profiles/itonami-maint/worktree`
   は stale/orphan (`.git` が `.../.git/worktrees/worktree` を指すがそのエントリは削除済み —
   git が fatal)。**正本は `~/.hermes/profiles/itonami-maint/wt-msloop`**
   (branch `bot/maturity-sim-loop`、`90-docs/sim-loop/status/maturity.md` + `evidence/`)。
2. **terminal の stdout は毎回空で返る** (exit 0)。だが **`> file` リダイレクトは機能する**。
   どんなコマンドも `cmd ... > /tmp/x.txt 2>&1; echo rc=$? >> /tmp/x.txt` にして
   `read_file` で読む。`execute_code` (hermes_tools python) は cron で BLOCKED。
3. terminal exit 128 (e.g. git) でも output が空 — 期待違反に惑わされず必ずリダイレクト確認。
4. `write_file`/`patch`/`search_files` が「sandbox still starting」/「missing path」で失敗する
   ／path を見失うことがある — 再発行で解消、リダイレクト + read_file が最安定。
5. patch は file 全読 (非ページング) が前提。巨大な maturity.md は python 置換
   (`open().read()/replace/write`) か write_file+`cat >>` で編集。
7. 運用/滞留軸の `ps aux | grep -E 'itonami-app-resident|export_and_sync'` は grep テキストが
   測定ハーネス自身 (hermes-snap の bash -c コマンド行) に一致して自助マッチ行を出し、それが
   実在の増加源と混ざる (falsify-99 で PID 93269/93285 を確認)。実増加源 (PID 70643) のみを
   拾い、自身のコマンド行ヒットは除外して報告すること。
8. dns-resolver annex の partial 一時ファイルは `.edn` 拡張子で `.git/annex/tmp/` に置かれる —
   `find -name '*.tmp' -o -name '*.part'` は一致せず 0 を返す **false negative** (falsify-121/122
   が「消滅」と誤測、falsify-123 で REFUTED)。partial 測定は必ず `git annex unused` +
   `ls .git/annex/tmp` の 2 法で行い、glob 単独は禁止。
7. `write_file` へ引数は path+content 両方必ず (片方欠けると missing field)。
7b. **append は `cat <tmpfile> >> target` 単文で行う (falsify-126 で事故)**。`cat >> file <<'EOF' ... EOF > /tmp/chk 2>&1` は末尾の `> /tmp/chk` が fd1 を上書きして **file への書き込みが完全に消える** (リダイレクトは後出しが勝つ)。また braced group `{ ...; } > chk` は Tirith セキュリティスキャンで BLOCK される。手順: (1) エントリを write_file で /tmp に書く、(2) `cat /tmp/entry >> target` + grep -c で確認 — 確認 grep は同一コマンド行に `>` リダイレクトで。stdout が
    空でも、リダイレクト無しの `echo ... >> file` / `cat f >> file` は**実行される**。確認用に同じ
    append を 2 度投げると二重追記になる — 追記コマンドは常に `{ ... } > /tmp/chk.txt 2>&1` に
    リダイレクトして 1 回だけ実行し、後続の独立コマンド (wc/tail/grep) は同じリダイレクト内に
    まとめて追加実行。二重追記した場合は自反復で入れた重複行に限り python で最初の
    `(evidence/...falsify-N.md)` 終端までで切り詰めて除去 (既存行は不触)。
7. append は heredoc (`cat >> file <<'EOF'`、EOF はクォート) で安全。EOF をクォートせず
   追記するとシェル展開が混入し、追記コマンドの残骸行 (例: `MD` / `echo "append rc=$?" ...`)
   が maturity.md 末尾に書き込まれる — falsify-91 で実際に発生 (行 1237-1238)。追記後は必ず
   `tail -3 file` を read_file で確認し、末尾に自分以外の残骸が無いか検眼する。既存の残骸は
   append-only 規約で編集せず、付記として next 追記内に記録して kanban/human へ透過報告する。

## 反復の流れ

1. `git -C wt-msloop log --oneline -3` で最新 falsify-N を確認。次は falsify-(N+1)。
2. `90-docs/sim-loop/evidence/` の最新を read して書式 (項目/判定/スコープ修正/附帯) を踏襲。
3. 7 軸の 1 つを測定、反証可能主張を立て falsify。可測は実コマンド出力を忠実記録、捏造ゼロ。
4. 判定: refuted → 範囲修正/修理案を maturity.md に追記 (Tier2 は提案のみ)、
   survived → 範囲を正確化して ledger 追記。score は測定で裏取れた時のみ上昇。
5. evidence/PATH (参照: falsify-56) → `git add` → `git commit` → `git push origin
   bot/maturity-sim-loop`。main checkout (agent/fix-open-red-5-three-bound) は touch 禁止。

## 作業境界 (SOUL 準拠)

- Tier 1: 決定論的検出+変換+テスト緑→着地可。Tier 2: 取得/測定/提案まで (着地は issue に)。
- Tier 3 (live gate 緩和、他者の未コミット WIP 接触) は禁止。
- ledger は追記のみ。本体 checkout が dirty の間は touch 禁止 (face-hash 系 7 ファイルは
  他 bot WIP)。変更前後でテスト緑確認。赤い間は測定と報告のみ。
- main 直 push 禁止。branch (bot/maturity-sim-loop) → commit+push。
