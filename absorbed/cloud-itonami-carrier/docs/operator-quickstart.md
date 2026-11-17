# operator quickstart

この repo は **R0 の propose-only actor skeleton** であって、稼働中のキャリア
システムではない（[README](../README.md) /
[ADR-0001](adr/0001-the-source-of-truth-this-readme-names-does-not-exist.md)）。
だから operator の仕事は「起動する」ことではなく、**この repo が名乗っている
拒否が今も本当に構造的かを確かめる**ことである。所要 3〜5 分（初回は依存の
ダウンロードで +1 分）。

必要なもの: **`clojure` CLI（JVM）だけ。** node も nbb も要らない。依存は
`deps.edn` の 3 つ（clojure / babashka.cli / cognitect test-runner）で、初回の
`kbb -M:test` が自分で取りに行く。

## 1. 取得する

```bash
git clone git@github.com:cloud-itonami/cloud-itonami-carrier.git
cd cloud-itonami-carrier
```

**ここに書いてあるのは素の `git clone` の方**である —— 空の clone から step 3 まで
通して実際に踏んだ手順だから（2026-09-05）。

west workspace の中なら `west update --fetch smart cloud-itonami-carrier` で
`orgs/cloud-itonami/cloud-itonami-carrier` に展開してもよい。その場合
**remote 名は `origin` ではなく `cloud-itonami`**（west が付ける名前）なので、
`git fetch origin` も `git log origin/main` も通らない。`cloud-itonami/main` と書く。

## 2. テストを走らせる（network は初回の依存取得だけ）

```bash
kbb -M:test
```

こうなれば緑:

```
Running tests in #{"test"}

Testing carrier.service.operation-test

Ran 6 tests containing 12 assertions.
0 failures, 0 errors.
```

見ているものは 6 つで、**5 つは「起きないこと」**である:

- **admitted な op はちょうど 5 つ**（`:subscriber/signup` `:subscriber/bill`
  `:subscriber/support` `:network/observe` `:outage/notify`）
- **未登録の op 名は throw する** —— ambient な op が無い。`propose` にも
  `govern` にも、名前を渡せば通る経路が無い
- **`propose` は実行しない** —— 返るのは `:pending-govern` であって `:done` ではない
- **`:propose` の op は自動実行されない** —— governor を通しても
  `:approved-for-review` で止まる。R0 に execution path は存在しない
- **`:network/observe` だけが govern 内で完了する**（純粋な観測だから）
- **SIM-swap の拒否が構造的である** —— `:ownership/transfer` /
  `:profile/download` / `:profile/lifecycle` が `op-names` に**そもそも無い**。
  拒否を実装しているのではなく、**実装する場所が無い**

最後の 1 つがこの repo の存在理由なので、ここが赤くなったら他が全部緑でも止める。

この run は `.cpcache/` を作る（`.gitignore` 済み）。**west の共有 checkout で
踏んでも tree は dirty にならない** —— dirty な checkout は `west update` に
拒否され、成熟度 scan にも「他セッションの WIP」として避けられるので、
quickstart が自分でそれを起こさないようにしてある。

## 3. governor を手で撃つ（30 秒）

```bash
kbb -M -e '(require (quote [carrier.service.operation :as op]))
(println "observe :" (:proposal/status (op/govern (op/propose :network/observe {}))))
(println "propose :" (:proposal/status (op/govern (op/propose :subscriber/bill {}))))
(println "swap    :" (try (op/propose :ownership/transfer {})
                          (catch clojure.lang.ExceptionInfo e (str "refused — " (.getMessage e)))))'
```

```
observe : :done
propose : :approved-for-review
swap    : refused — op not admitted
```

**3 行目が肝である。** `:ownership/transfer` は「拒否される op」ではなく
**op ではない**。この repo に SIM-swap を実行する経路が無いのは policy が
そう決めているからではなく、`ops` に無い名前を `propose` に渡すと
`ex-info` が飛ぶからである。policy は書き換えられるが、無い関数は呼べない。

拒否の authority 本体は `cloud-itonami/cloud-itonami-esim` に在る（次節）。
ここが持っているのは**その拒否を上書きしない**という性質だけである。

## 4. 境界の主張を自分で引く（2 分）

README の「担わないもの」は、他 repo に authority が実在することを前提に
している。**前提は前提として引ける。** 2026-09-05 に引いた結果は ADR-0001 §4 に
在るが、値ではなく**引き方**を写す —— 値は古くなる。

```bash
# (a) esim の構造的拒否。phase 3 の :auto に何が入っているか
grep -n ':auto' <workspace>/orgs/cloud-itonami/cloud-itonami-esim/src/esimprovisioning/phase.cljc
# → :ownership/transfer がどの phase の :auto にも無いこと。
#   test/esimprovisioning/phase_test.clj がそれを固定していること

# (b) 決済委譲先が west に在るか
grep -A3 'name: nexus-x402$' <workspace>/manifest/west.yml
# ⚠ 在るのは登録であって中身ではない。checkout していないなら中身は未測定

# (c) 人的対応の外注先 ADR
ls <workspace>/orgs/cloud-itonami/cloud-itonami-app/docs/adr/ | grep 0084
# ⚠ その repo には 0084 が 2 本在る。番号でなくファイル名で引く
```

`<workspace>` は superproject root。**素の clone だけを持っているなら、この節は
踏めない** —— その場合 (a)(b)(c) は「未測定」であって「真」ではない。

## 5. 緑が言っていないこと（読む前に必ず）

**`0 failures` は「検査されている」という意味ではない。** この repo について、
今日の時点で緑が何も言っていない領域が 3 つ在る（ADR-0001 §2・§3・§5 が測定）:

1. **`blueprint.edn` と `src/` の食い違い。** 両者は同じ 5 op を宣言しているが、
   テストは `blueprint.edn` を読まない（op 集合を自分の中に literal で持つ）。
   **片方だけ編集すると、両方が緑のまま食い違う。**
2. **mutation runner の緑。** superproject で
   `kbb --backend sci scripts/maturity-loop/run.cljk --only cloud-itonami-carrier` を回すと
   `0 suite` / `噛まない=0` / **exit 0** が返るが、これは
   「登録が 1 件も無い」の意味である。**「全部噛んだ」と同じ形をしている。**
   この緑をテスト品質の証拠に使わない。
3. **PR 規律。** README は「main 直 push なし」と書くが、`gh pr list --state all`
   は今のところほぼ空である。規律は破られていないが、**まだほとんど試されていない**。

## 赤くなったら

**壊れたとは限らない。境界が動いたのかもしれない。**

1. 失敗行を読む。§2 の 6 項目のどれが落ちたかで意味が違う
2. **SIM-swap の構造的拒否（`sim-swap-refusal-is-structural`）が落ちたなら、
   そこで止めて owner に報告する。** これは「テストが古い」で通してよい
   種類の赤ではない —— 誰かが `ops` に line-mutating な op を足したという意味である
3. 他の赤は、`blueprint.edn` / `src/` / テストの 3 点のうちどれが正しいかを
   先に決める。**テストを実体に合わせて直す前に、実体が正しいかを決める**
4. 何がどちらへ動いたかを commit message に書く

## やらないこと

- **`:propose` の op に execution path を足さない。** R0 に外部接続は無い。
  wholesale 相手が実在するまで、実行系のコードをこの repo に書かない（README「段階」）
- **eSIM のプロファイル操作をここに実装しない。** authority は
  `cloud-itonami-esim` に在り、その拒否は永続である。ここに再実装した瞬間、
  拒否は 1 箇所ではなくなる
- **coverage を自前で計算しない。** 真実は wholesale 相手と Starlink の
  公開 coverage map の側に在る（README「担わないもの」）。自前計算は
  作った瞬間に嘘になる
- **§5 の 3 つを、作業せずにチェックだけ埋めない。**
