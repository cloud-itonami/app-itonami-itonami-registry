# digest の形式 (JUN-525 / JUN-526 の前提)

初回稼働の出力と、dapp が読む入力の形を先に決める。bot は digest を **ローカルの workspace** に作り、
外部へ送らない。dapp はこの形をブラウザ側で読む。形式が変わるときは `schema` の版を上げる。

## 構造 (EDN)

```clojure
{:schema "compute-energy-watch.digest.v1"
 :generated-at "2026-10-28T00:00:00Z"        ; digest を作った時刻
 :previous-digest-ref nil                     ; 前回 digest の CID または相対パス。初回は nil
 :entries
 [{:id :gpu.supply.sales                      ; docs/metrics.md の id
   :value-kind :published-estimate            ; :measured | :published-estimate | :own-estimate | :unknown
   :value nil                                 ; :unknown のとき nil。数値は単位とセットで書く
   :unit nil                                  ; 出典に書かれた単位。確認できないときは nil
   :period nil                                ; 対象期間（出典の記載どおり）
   :source {:name "Epoch AI: AI chip sales"
            :url "https://epoch.ai/data/ai-chip-sales"
            :license "CC BY"                  ; data-sources.md の区分の根拠
            :retrieved-at "2026-10-28"        ; 取得日
            :source-updated "2026-10-21"}     ; 出典の最終更新日（記載があれば）
   :estimate nil                              ; :own-estimate のときだけ {:formula "…" :assumptions […]}
   :delta nil                                 ; 前回との差。初回は nil
   :note nil}]}                               ; 注意点。因果は断定しない
```

## 規則

- `:value-kind` が `:unknown` の entry は `:value` を持たない。`UNKNOWN` を数値で埋めない。
- `:source` は必須。`:retrieved-at` と `:url` を欠く entry は書かない。
- `:own-estimate` は `:estimate` に式と前提を持つ。出典の値と混ぜない。
- `:published-estimate` は出典が推計と明記したもの。`:measured` と書かない（Epoch AI の値は推計）。
- ライセンスが `verified` でない源の entry は作らない（metrics.md の `UNKNOWN` のまま）。
- digest に個人情報・資格情報・会話内容を入れない。
- 投資助言に当たる記述（売買の推奨、価格予測の売買判断への利用）は `:note` にも書かない。

## 初回稼働の手順 (JUN-525。承認後)

1. owner が取得を承認する。表示する内容: サービス `epoch.ai`、endpoint `https://epoch.ai/data/ai-chip-sales`
   への GET 1 回、データ区分は公開データの取得のみ（送るユーザーデータなし）。
2. 取得した値を、ページに書かれた単位・期間・最終更新日のまま entry に書く。確認できない項目は nil とし、
   metrics.md の `要確認` を更新する。
3. 値を出典ページと見比べて読み戻す（数値、単位、期間、日付）。
4. 食い違いがあれば digest を直し、直せなければ entry を `:unknown` にする。
5. 結果と、registry の validation 記述（runtime）に反映するかを owner に諮る。

## dapp (JUN-526) との関係

dapp は、この EDN をブラウザ側で読んで表示する。外部取得を dapp が行う場合は、取得ごとに
`kotoba.app.client-runtime.v1` の descriptor に宣言した operation と都度承認を通す。
app origin に request-time 処理を置かない。
