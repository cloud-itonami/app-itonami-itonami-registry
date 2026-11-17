# compute-energy-watch 設計 (JUN-495)

世界の電力・CPU・network・storage・GPU の生産/供給・需要・消費を、公開出典だけから
分析する itonami bot profile の設計。Linear: JUN-495。

## 状態

- 起票 2026-10-28。profile 定義は `hermes/profiles/compute-energy-watch/`。
- データ源の権利状況は 2026-10-28 に一部確認済み（下の「データ源と権利状況」）。`verified` 以外の源は
  bot が取得しない（SOUL.md 手順 2）。
- ランタイム未検証。レジストリ登録は「定義の公開」であり、稼働や権限を意味しない。

## 指標の分類

3 軸 × 5 資源クラス。各指標は `id`・単位・対象期間・頻度・出典を持つ。

| 軸 | 電力 | CPU | network | storage | GPU |
|---|---|---|---|---|---|
| 生産/供給 | 発電量、設備容量 | 出荷、ウェハ生産能力 | 敷設・稼働中の国際回線容量 | HDD/SSD/NAND 出荷、ウェハ生産能力 | 出荷、先端パッケージ能力 |
| 需要 | 系統需要、DC 向け需要 | サーバ需要 | トラフィック需要 | 保存需要 | 学習・推論の計算需要 |
| 消費 | 部門別消費、DC 消費 | 稼働 CPU | 実トラフィック | 稼働保存量 | 稼働 GPU、クラスタ容量 |

指標の値は次のいずれかとして記録する。混ぜない。

- `measured`: 出典が公表した実測値
- `published-estimate`: 出典が公表した推計
- `own-estimate`: bot の推定（式と前提を必ず併記）
- `UNKNOWN`: 取得できない

## データ源と権利状況

2026-10-28 に主要な源の公開条件を確認した。詳細と根拠は [`data-sources.md`](data-sources.md)。
区分は `verified` / `restricted` / `excluded` / `unverified`。

| 区分 | 源 |
|---|---|
| `verified` | EIA、Ember、Epoch AI（承認を得た上で取得可。取得時に個別条件を再確認） |
| `restricted` | IEA（無料報告書の CC BY 4.0 部分のみ）、ITU（統計は許諾が必要）、TeleGeography の地図（CC BY-SA）、Cloudflare Radar（CC BY-NC 4.0） |
| `excluded` | WSTS、TeleGeography のデータ（有料）、SEMI World Fab Forecast |
| `unverified` | ENTSO-E、TOP500、SIA、SEMI の公表資料、IXP の公開統計 |

CPU・network・storage に `verified` な源はまだない。該当する軸は `UNKNOWN` とする。
有料レポート（調査会社のサブスクリプション等）は、契約がない限り対象外。

## 既存 repo との責務境界

| repo | 担当 | 本 profile との関係 |
|---|---|---|
| `energy-order` | 有用フローの検証と報酬提案 | 入力や出力を共有しない。重複指標を見つけたら報告する |
| `datacenter`, `data-center-ops` | 施設単位の運用判定・依存関係 | 施設の実測は扱わない。世界集計の参考にのみ参照する |
| `handotai` | 半導体 appview の scaffold | 表示面。必要なら digest を読ませる（別 issue） |
| `app-open-power` | 配電網の設計・運用 | 局所の運用。範囲外 |

`app-open-power` は README 冒頭だけ確認した（配電網の設計と運用、停電・検針）。世界の
需給分析は含まない。

## dapp の前提 (JUN-526)

共有 runtime `kotoba-lang/wasm-webcomponent/src/kotoba-client-runtime.js` は origin/main に存在する
（PR 26 で merge 済み、2026-10-28 に `git ls-tree origin/main` で確認）。ローカルの checkout が古いと
見えないので、確認は origin/main に対して行う。dapp は独自のコピーを作らず、この実装を取り込む。
digest の形式は [`digest-format.md`](digest-format.md) に定めた。初回稼働（JUN-525）の後に dapp の実装へ着手する。

## 外部アクセスとプライバシー

- 取得は外部 operation として、取得ごとに承認を得る。サービス、endpoint、データ区分を
  事前に提示する。拒否されたら何も送らない。
- 推論は murakumo rail のみ。遠隔推論へのフォールバックはしない。
- app origin に処理を置かない。digest はローカルの workspace に作る。

## 出力

定期 digest（日次/週次は運用で決める）。構成: 更新指標、UNKNOWN 指標、前回差分、使用出典、
次の取得期限。投資助言に当たる記述はしない。

## 受入条件との対応 (JUN-495)

| 受入条件 | 状態 |
|---|---|
| 対象指標・データ源・出典ポリシーの設計文書 | この文書と data-sources.md。権利確認は主要 10 源のうち 3 源が verified。指標表は metrics.md（電力・GPU のみ。CPU・network・storage は UNKNOWN） |
| registry 登録と安全な初回稼働の読み戻し | 登録は PR で行う。初回稼働は未実施 |
| 出典と取得日、推定と実測の区別 | SOUL.md と本書に規則を記載。運用での検証は未了 |
| 投資助言をしない | SOUL.md と yakuwari.edn で禁止。運用での検証は未了 |

## 残り

1. CPU・network・storage の `verified` な源は未発見（JUN-535 の探索結果）。許諾申請は owner 判断。
2. 指標表の初期セットの確定（JUN-524）。
3. 初回稼働（承認付き、1 指標）と読み戻し（JUN-525）。
