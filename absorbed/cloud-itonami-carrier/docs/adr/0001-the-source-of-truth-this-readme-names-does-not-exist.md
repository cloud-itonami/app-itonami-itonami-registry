# ADR-0001 — この README が名指す正本は存在しない

- **status**: accepted
- **date**: 2026-09-05
- **参照**: superproject `adr-2800010200-cloud-itonami-carrier-west-registration`
  （この repo の west 登録） /
  `adr-2608052000-itonami-maturity-dependency-system-dynamics`（成熟度の測り方） /
  `adr-2608080000-itonami-maturity-improve-loop`（1 反復 1 軸）
  —— **番号だけで引かない。** superproject には `2608052000` も `2608080000` も
  別主題の ADR が同じ番号で在る（既知の採番衝突）
- **先例**: `cloud-itonami/marine-insurance` ADR-0001
  （同型の「名乗りと実体の差を測る」snapshot）

## 文脈

この repo は 2026-09-01 に R0 scaffold として 1 commit で起こされた
（`d49627a`）。README・`blueprint.edn`・`src`+`test` が同時に入り、
その日のうちに west manifest に登録された。

README の冒頭は **「ADR-2609011500 が正本」** と書いている。R0 の repo が
外部の ADR を正本として指すのは正しい形である —— この repo には設計判断を
記録する場所がまだ無く、判断は superproject 側に在るはずだからである。

**問題は、その ADR が無いことである。**

## 測ってわかったこと（2026-09-05）

### 1. 名指された正本が、木のどこにも無い

```bash
git grep -l "2609011500" origin/main    # → 0 件
```

sparse checkout の外に在るのではない —— `origin/main` の木全体に対して引いて
0 件である（手元に無いことと存在しないことを混同しないための引き方。
superproject AGENTS.md「『無い』と結論する前に検索する」）。

**この repo について実在する superproject ADR は 1 本だけ**で、それは
`90-docs/adr/2800010200-cloud-itonami-carrier-west-registration.edn`
（`:adr/status "accepted"`、2026-09-01）である。そして**その ADR は自分が
正本ではないと明記している**:

> 携帯キャリア事業の運用本体 (esim/x402 delegation, starlink direct
> wholesale 前提) は cloud-itonami/carrier-itonami bot の管轄。
> **この ADR は三点同期の登録のみを記録する。**

つまり README が述べている設計判断——自前 spectrum を持たない構成、
esim actor への provisioning 委譲、x402 への決済委譲、coverage を
自前計算しないという選択、R0/R1/R2 の段階——は、**どの ADR にも
記録されていない。** 読み手が「なぜそう決めたか」を辿る先が無い。

存在しない ADR 番号を名指すのは、記録が無いことより悪い。**無いことが
見えなくなる**からである。番号が書いてあれば、読み手はそれを引かずに
「記録は在る」と読む。

### 2. `blueprint.edn` と `src/` は一致しているが、確かめる者が居ない

両方が同じ 5 op（`:subscriber/signup` `:subscriber/bill` `:subscriber/support`
`:network/observe` `:outage/notify`）を、同じ effect class で宣言している。
2026-09-05 時点で**実際に一致している**。

しかし `test/` は `blueprint.edn` を読まない（`grep -rn blueprint test/ src/`
→ 0 件）。テストは op 集合を自分の中に literal で持っている。したがって
**片方だけを編集すると、両方が緑のまま食い違う。** 宣言（blueprint）と
実装（src）が別々の真実を語り始めても、何も赤くならない。

これは次の反復（`axis-test`）の仕事であって、この ADR では記録だけする。

### 3. mutation runner の緑は、この repo については「未測定」の意味である

superproject の `scripts/maturity-loop/run.cljs` は「テストを壊して赤くなるか」
を確かめる道具で、この workspace が `axis-test` の gate として使っている。

```bash
kbb --backend sci scripts/maturity-loop/run.cljk --only cloud-itonami-carrier
# maturity-loop: 0 suite / policy maturity-loop/mutation/v1
# maturity-loop: 噛む=0 噛まない=0 エラー=0 skip=0     ← exit 0
```

`mutations.edn` にこの repo の項目が 1 つも無いので、**「登録が無い」が
「全部噛んだ」と同じ形（exit 0・噛まない=0）で返る。** superproject
AGENTS.md が繰り返し名指ししている形——*測れなかった検査が、測って問題が
無かった検査と同じ値を返す*——そのものである。

**この緑をテストの品質の証拠として引用しない。**

### 4. 境界の主張 3 本は、実測して真だった

README の「担わないもの」は、他 repo に authority が実在することを前提に
している。3 本とも引いた:

| 主張 | 実測 |
|---|---|
| eSIM lifecycle は `cloud-itonami-esim` が持ち、SIM-swap を構造的に拒否する | **真**。`src/esimprovisioning/phase.cljc` の phase 3 は `:auto #{:euicc/register}` だけで、`:ownership/transfer` はどの phase の `:auto` にも無い。`test/esimprovisioning/phase_test.clj` がそれを固定している |
| 決済は `network-awai/nexus-x402` に委譲する | **登録は真**。west manifest に `nexus-x402`（`orgs/network-awai/nexus-x402`、pin `739793be`）が在る。⚠ 手元に checkout が無いので、**確かめたのは登録であって中身ではない** |
| 人的対応は `cloud-itonami-app` の ADR-0084 市場に外注する | **真**。`docs/adr/0084-human-work-assurance-marketplace-and-held-payouts.md`（accepted、2026-08-31）。⚠ その repo には **0084 が 2 本在る**（もう 1 本は domain-steward）ので、番号でなくファイル名で引くこと |

そして**継承は「op が無いこと」として実装されており、それは実際にテストされて
いる** —— `sim-swap-refusal-is-structural` が `:ownership/transfer` /
`:profile/download` / `:profile/lifecycle` が `op/op-names` に無いことを固定する。
R0 が外部に繋がらない以上、拒否を継承する唯一の正直な方法がこれである。

### 5. 「1 task = 1 branch = 1 PR」は、まだ一度も行使されていない

README の規律節は「main 直 push なし」と書くが、`main` は commit 1 本
（scaffold そのもの）で、PR は全 state を通して 0 件である
（`gh pr list --state all` → `[]`）。scaffold commit 自体が直 push である。

規律が破られたという話ではない——**まだ一度も試されていない**という話で、
この ADR を載せる PR がその 1 本目になる。

## 決定

1. **README の「ADR-2609011500 が正本」を撤回する。** 実在する
   `adr-2800010200`（west 登録のみ）と、この ADR-0001（repo 側の設計記録）を
   指すように直す。**存在しない番号を、別の存在しない番号に置き換えない。**
2. **repo 側の設計判断は、当面この `docs/adr/` が正本とする。** superproject に
   運用本体の ADR が起きたら、その時に本 ADR を `superseded` にして指す。
3. **上の測定 2・3・5 は塞がずに記録する。** 1 反復で 1 軸しか上げないので
   （`adr-2608080000-itonami-maturity-improve-loop`）、この反復の成果物は
   docs だけである。
   塞ぐ順序は 2（blueprint↔src の drift 検査）→ 3（mutation 登録）。

## 帰結

- 「なぜこの構成なのか」を読み手が辿れる場所が、この repo の中にできた。
- **`docs/operator-quickstart.md` が、上の測定を operator が自分で再実行できる
  形で持つ。** ここに書いた実測値は 2026-09-05 のものであって恒久の性質では
  ないので、引用ではなく**引き方**を残す。
- 塞いでいない穴が 3 つ、日付つきで名前を持った。

## やらないこと

- **無い ADR を、内容を推測して書き起こさない。** 設計判断をしたのは
  `carrier-itonami` bot と owner であって、この反復ではない。ここが記録して
  よいのは「記録が無い」という測定結果までである。
- **blueprint↔src の drift 検査を、この反復で足さない。** それは `axis-test`
  であって `axis-docs` ではない。軸を混ぜると、どちらも実演されないまま
  両方が「上がった」ことになる。
- **R1 / R2 に進まない。** wholesale 相手が実在するまで、外部接続を持つ
  コードをこの repo に書かない。
