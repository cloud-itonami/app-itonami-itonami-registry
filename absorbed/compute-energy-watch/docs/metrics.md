# 指標表（初期セット） (JUN-524)

確認日: 2026-10-28。`verified` な源（EIA、Ember、Epoch AI。[`data-sources.md`](data-sources.md)）から
取れる指標だけを載せる。**列のうち単位・系列名・頻度は、各データセットのページで確認できたものだけを
書き、確認できないものは `要確認` とする。** 確認は初回稼働（JUN-525）で行い、確認後にこの表を更新する。

値の種別は `measured`（出典の実測値）/ `published-estimate`（出典の推計）/ `own-estimate`（bot の推定。式と前提を併記）/
`UNKNOWN`（取得できない）のどれか。取得は都度の承認が必要。

## 電力

| id | 軸 | 内容 | 出典 | 単位・頻度 | 種別 |
|---|---|---|---|---|---|
| `power.generation` | 生産/供給 | 国別・電源別の発電量 | Ember: Electricity Data Explorer / Monthly electricity data (https://ember-energy.org/data/) | 要確認（月次データあり） | published-estimate または measured（出典の記載を確認） |
| `power.capacity` | 生産/供給 | 設備容量 | Ember: Electricity Data Explorer | 要確認 | 同上 |
| `power.demand` | 需要 | 国別の電力需要 | Ember: Electricity Data Explorer / Monthly electricity data | 要確認 | 同上 |
| `power.consumption` | 消費 | 国別・部門別の消費 | EIA International (https://www.eia.gov/international/) | 要確認。API は鍵の要否を確認 | 要確認 |
| `power.datacenter` | 消費 | データセンタの電力使用 | Epoch AI: AI data centers (https://epoch.ai/data/ai-data-centers) | 要確認（衛星・許可データに基づく推計） | published-estimate |

## GPU

| id | 軸 | 内容 | 出典 | 単位・頻度 | 種別 |
|---|---|---|---|---|---|
| `gpu.supply.sales` | 生産/供給 | AI チップの販売に基づく計算量・電力・支出の推移 | Epoch AI: AI chip sales (https://epoch.ai/data/ai-chip-sales) | 要確認。最終更新 2026-10-21 | published-estimate（財務報告・企業開示に基づく） |
| `gpu.supply.specs` | 生産/供給 | AI アクセラレータの仕様（180 超） | Epoch AI: Machine learning hardware (https://epoch.ai/data/machine-learning-hardware) | 要確認。最終更新 2026-10-26 | published-estimate |
| `gpu.demand` | 需要 | 計算需要 | — | — | `UNKNOWN`（verified な源なし） |
| `gpu.consumption.clusters` | 消費 | GPU クラスタ・スーパーコンピュータ（500 超） | Epoch AI: GPU clusters (https://epoch.ai/data/gpu-clusters) | 要確認。最終更新 2026-03-13 | published-estimate |
| `gpu.consumption.users` | 消費 | 利用者別の計算力（H100 換算） | Epoch AI: AI chip users (https://epoch.ai/data/ai-chip-users) | H100e。最終更新 2026-09-09 | published-estimate |

## CPU / network / storage

`verified` な源がまだない。現時点では全軸を `UNKNOWN` とする。

| 資源 | 軸 | 状態 | 次の手 |
|---|---|---|---|
| CPU | 生産/供給、需要、消費 | `UNKNOWN` | WSTS と SEMI World Fab Forecast は `excluded`。SIA は規約を読めず `unverified`。各社決算（出典ごとに権利確認）が次の探索先 |
| network | 生産/供給、需要、消費 | `UNKNOWN` | ITU は許諾が必要、TeleGeography データは有料、Cloudflare Radar は CC BY-NC 4.0（非営利のみ。商用可否は owner 判断）。IXP は統計ページごとの規約確認が次の探索先 |
| storage | 生産/供給、需要、消費 | `UNKNOWN` | 出荷統計は商用調査会社のもの（`excluded`）。各社決算の公開資料が次の探索先 |

## 規則

- 同じ id の値を別の源で埋め直すときは、源を併記し、元の値を消さない。
- 前回 digest との差分を必ず書く。因果は断定しない。
- `power.datacenter` と `gpu.consumption.*` は別の源の推計なので、足し合わせない。
- `gpu.*` の値は Epoch AI の推計であり、`measured` と書かない。
- 出典の更新日がこの表の日付より新しい場合は、digest に取得日と出典の最終更新日を両方書く。

## 受入条件との対応 (JUN-524)

| 条件 | 状態 |
|---|---|
| 5 資源クラスに最低 1 指標、取れない軸は UNKNOWN | 電力・GPU は指標あり。CPU・network・storage は全軸 `UNKNOWN`（上記の理由） |
| 各指標の出典 URL・単位・頻度 | 出典 URL は記載。単位・頻度の多くは `要確認`（初回稼働で確定） |
| docs/metrics.md として PR merge | この文書 |

CPU・network・storage の源探し（JUN-535）では `verified` な源が見つからなかった（[`data-sources.md`](data-sources.md)）。
5 資源クラス全てに指標がある状態にするには、owner による許諾申請の判断か、追加の探索が必要。
