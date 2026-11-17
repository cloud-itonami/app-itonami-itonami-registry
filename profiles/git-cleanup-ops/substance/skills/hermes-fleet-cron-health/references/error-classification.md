# last_error → 対応 決定表

> Current owner policy: use Murakumo/Mishima only with `fallback_providers: []`. Do not switch to OpenRouter, Kotoba API, peer inference, or another external route. If Murakumo cannot serve the configured request, stop and report; never copy secret values between profiles.

`last_error` の substring か、その `last_status` / `failure_streak` からどう扱うかを
一方向で決める。**後で loadavg を見る前に**これを当てて buckets を先に数え、
その後で host 要因として一括解釈する。間違えやすい3つ（shutdown / drift_skip /
script-not-found）は太字。

| last_status | last_error substring | 分類 | 扱い |
|---|---|---|---|
| error | **"Gateway shutdown" / "Interrupted by shutdown"** | interrupt 巻き添え | host 過負荷・ゲートウェイ再起動波の self-heal。load 落ちても streak 伸び続ける時だけ真の障害 |
| error | **"drift_skip" / "Skipped to prevent unintended spend"** | 費用手ガード | 意図的スキップ、次 tick で再実行。修正不要。error 率計算前に分離 |
| error | "Connection error" | conn | provider・key_env 名と credential presence metadata だけを確認し、秘密値は読まない / コピーしない。Murakumo 認証に問題があれば owner に報告 |
| error | "Broken pipe" / "connection_refused" | transient conn | gateway 再起動と cron 発火の競合。Murakumo 503 "Loading model" も同型。ログで原因を確認し、停止中 / disabled job は再 fire しない。再試行が必要なら owner 承認を得てから行う |
| error | "REFUSED" | refused | script 側の前提不成立（対象不在など）。スケジューリングではない |
| error | "Script not found: ...scripts/<n>" | script | まず `ls <profile>/scripts/<n>` で実在を確認。実在なら stale 残滓で既に治癒 → 再 fire |
| error | "TERMINAL_CWD read lock" / "Timed out waiting" | lock / timeout | 共有 workdir の衝突 or 過負荷の遅延 |
| error | 上記以外 | other | 個別に logs/agent.log の最後の成功ツールコールまで遡る |
| ok / None | — | — | None は NEVER_RUN。作成<7d + next既来 = 正規保留、+ 古く next過去 = stalled |

## streak 成長の時系列検出（常駐ヘルス bot）

`last_status` は最新だけを見せるので「巻き添えで1回吐いた」と「真に壊れ続けて」を
区別できない。ふたつのスキャンの間に `failure_streak` が**増えた job だけ**を報告する:

- 各 job の `failure_streak` を `<profile>/cron/jobs.json` から読んで `state-snap.json`
  （measure bot 自身の workspace に置く）と比較し、増分 >0 を `streak_grown` として出す。
- 全 job を毎時走らせ、`cron-health-ledger.jsonl` のような append-only ledger に
  ok/error/drift/never の内訳 1 行を追記する。
- 初回スキャンの streak_grown は「前回なし→今回」の全量になる。次回から差分になるだけ
  — 初回結果を真の故障リストとして出さない。

## 実測したベースライン（負荷を引いて判断）

10 コアのホストで loadavg ~72〜75（比 7x）のとき、177 jobs 中
- ok 111 (62.7%) / error 41 のうち drift_skip 10・interrupt 22・conn 2・refused 1・script 1・lock 1
- 真に直すべきは片手に収まる(単発 conn/refused/script + 高 streak の数件)。
「error = 壊れてる」と素直に数えると健康な fleet を数十件の障害と読み違える。

## executions.db の failed は scheduler ログと食い違うことがある（実測 2026-09-06）

webest-deploy-watch が executions.db で今日 10 回連続 failed（Interrupted）表示かつ
streak=10 だったが、scheduler の正本 agent.log では同日 13:03 / 14:29 / 16:16 に
「Job completed successfully」し webest bot chat に配信済み。executions.db の行は
stale / 二重実行の競合で failed のまま残る。**個別 job の最終判定は logs/agent.log
 の scheduler 行（`Job '<name>' completed successfully`）を正本にする。**
cron-health の streak 検出は「要因が agent.log で裏取れた時だけ真の障害」と報告する。

## config.yaml のモデルを変えると unpinned job が drift_skip になる（実測 2026-09-06）

config.yaml の `model.default` を変更すると、その profile の **unpinned cron job が全部
`drift_skip` し始める**（scheduler.py が job 作成時の model_snapshot/provider_snapshot と
現 config を比較し、変わった job をフェイルクローズで skip — 意図しない出費を防ぐ）。
これは「config 差し替え」後の正常ガードであって障害ではないが、対処が必要:

- pin 済み job（`model:`/`provider:` が jobs.json に書かれ、snapshot が None）は drift しない。
- unpinned job は `hermes cron edit <id> --provider <p> --model <m>` で pin すれば
  snapshot が None になり、以降 drift しない。
- fire しても `Ran now: failed` のまま `[drift_skip]` が出る時は、edit 後の in-memory
  config が古い可能性 — scheduler が稼働中なら次の実 tick で反映される。手動 fire は
  別プロセスだが config 読込で fresh。実行中は `running` で進むのを待つ。
- 意味論: URL などでなく snapshot(=作成時グローバル config) と現在値を比較。
  snapshot が None の pin 済みは「変更に追従する」仕様なので動く。

実例（同一 fork で 3 件同時発生）: あるセッションが pr-cleanup の config を
glm→deepseek(nous) に変更した。glm に pin 済みだった pr-queue-review は provider 軸が、
unpinned の pr-queue-pulse は model 軸が drift し、両方 skip になった。
これは歴史的な 2026-09-06 の事例であり、provider 切替手順として再利用しない。現在は Murakumo/Mishima と `fallback_providers: []` を維持する。

関連: `murakumo-main` の `all-slots-busy 429`（capacity 2）は共有 slot 競合。webdesign 等
が詰まっても非-Murakumo provider へ切り替えない。停止して owner に報告する。

## 旧 OpenRouter 切替記録（historical only）

以下の旧運用は撤回済みで、profile の現在の手順として実行しない。OpenRouter を選ぶ、fallback を増やす、または external provider へ切り替える操作は禁止。設定差分の調査では現行の Murakumo/Mishima 設定だけを確認し、fallback は空のままにする。容量・モデル・認証の問題は停止して owner に報告する。

## 旧単一 provider routing 記録（historical only）

OpenRouter 固定経路に関する過去の測定値であり、現在の route 変更を指示しない。現在の owner policy は Murakumo/Mishima のみ、`fallback_providers: []`。provider-routing 設定を変更して外部自動分散へ戻さない。問題が起きたら停止して報告する。
