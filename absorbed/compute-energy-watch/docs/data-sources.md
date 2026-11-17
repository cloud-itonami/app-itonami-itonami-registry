# データ源の利用条件 (JUN-523)

確認日: 2026-10-28。公式ページ（または検索で得た公式説明）を読んだ結果で、**法的助言ではない**。
条件は変わりうるため、`verified` でも取得時に当該データセットのページで個別条件を再確認する。

## 区分

| 区分 | 意味 | bot の扱い |
|---|---|---|
| `verified` | 公開条件が、出典付きの取得・要約・再掲を許すと読める | 承認を得た上で取得してよい |
| `restricted` | 一部のみ許される、または別規約・別手続きが必要 | 許される部分だけ。範囲外は取得しない |
| `excluded` | 有料、または許諾がなければ再利用できない | 取得しない |
| `unverified` | 条件を読めていない | 取得しない |

## 結果

| 源 | 区分 | 根拠 | 条件・注意 |
|---|---|---|---|
| EIA (米エネルギー情報局) | `verified` | https://www.eia.gov/about/copyrights_reuse.php | データ・報告書は米国政府著作物で、通常は自由に利用・再配布できる。出典表示（EIA と公表日）が求められる。第三者の資料・写真・ロゴは対象外 |
| Ember | `verified` | https://ember-energy.org/about/licensing/ | サイトの全コンテンツが CC BY 4.0。出典表示が必要。名称は商標。個別データのページも取得時に確認する |
| Epoch AI | `verified` | https://epoch.ai/data | データセット（GPU クラスタ、ML ハードウェア等）は CC BY。出典・著者表示が必要。外部リンク先の資料は別扱い。取得時に各データセットのページで再確認 |
| IEA | `restricted` | https://www.iea.org/terms | 無料の本文・報告書・単独の図は CC BY 4.0。**単独のデータセット、data explorer、データベース、WEO のデータ annex は CC BY 4.0 の対象外**で別規約。ロゴ・画像も対象外。自動アクセスは拒否されうる。AI エージェントには別の AI Agent Terms がある |
| ITU | `restricted` | https://www.itu.int/en/Pages/copyright.aspx | 一般規定のみ。統計・出版物の再利用は許諾の申請が必要（jur@itu.int）。報道資料は ITU を出典に明記すれば可 |
| TeleGeography | `excluded` (データ) / `restricted` (地図) | https://www2.telegeography.com/cite-telegeography-map | 公開地図は CC BY-SA 4.0。背後のデータは有料ライセンス。地図の再利用は SA の条件を満たす場合のみ |
| WSTS | `excluded` | https://www.wsts.org/ | 全出版物が WSTS の著作物で、許諾なしの複製は禁止。無料の Historical Billings Report にも再利用の明示許諾はない。月次レポートは会員限定 |
| ENTSO-E Transparency Platform | `unverified` | 二次資料のみ（現行の利用規約ページを読めなかった） | 2019 年以降、TSO のデータは open data licence で公開する方針とされるが、全データに及ぶかは争いがあり、標準の CC ライセンスではないという指摘もある。現行の Terms and Conditions を読むまで取得しない |
| TOP500 | `unverified` | https://www.top500.org/, https://www.top500.org/project/ | 利用条件の記載がなく、著作権表記（Copyright 1993-2026 TOP500.org）のみ。許諾なしの再利用可否は不明。取得しない |
| SEMI（World Fab Forecast） | `excluded` | https://www.semi.org/en/products-services/market-data/faqs | 派生物は社内利用のみ。外部公開は SEMI の許諾が必要（個別審査）。公表する digest に使えない |
| SEMI（装置 billings の公表資料） | `unverified` | — | 再利用方針を確認できなかった。問い合わせ先は mktstats@semi.org |
| SIA | `unverified` | — | 利用規約ページを読めなかった（推測した URL が 404）。取得しない |
| Cloudflare Radar | `restricted` | https://radar.cloudflare.com/about （直接は 403。Cloudflare の開発者文書と about ページの記述を検索経由で確認） | Radar API と直接ダウンロードのデータは **CC BY-NC 4.0**（非営利のみ）。埋め込みグラフ・画像は CC BY 4.0。商用の可否は例外申請の窓口が about ページにある。bot の digest が商用に当たるかは owner 判断 |
| IXP の公開統計（DE-CIX、AMS-IX、LINX 等） | `unverified` | — | 現行の利用規約を見つけられなかった。IXP ごとに統計ページと規約を確認する必要がある |
| ストレージ出荷の統計（Trendfocus 等の調査会社） | `excluded` | — | 商用の調査レポートで、転載記事にも利用条件の記載がない。公開データではない |

## 帰結

- 今すぐ取得してよい候補は **EIA、Ember、Epoch AI** のみ（いずれも承認を得た上で）。
- 電力は EIA と Ember、GPU/計算は Epoch AI でカバーできる。**CPU、network、storage は、現時点で `verified` な源がない。** これらの軸は `UNKNOWN` のままにする。
- IEA は、無料報告書の CC BY 4.0 部分のみ。データセットの自動取得はしない。
- 半導体（CPU・storage の出荷・製造）と network の公開データは、許諾を取るか、別の源（各社決算など、出典ごとの確認）を探す必要がある。

## CPU・network・storage の源探し (JUN-535) の結論

2026-10-28 の探索では、**3 資源クラスのいずれにも `verified` な源は見つからなかった**。

| 資源 | 見つからなかった根拠 |
|---|---|
| CPU | WSTS と SEMI の World Fab Forecast は外部公開に許諾が必要。SIA は規約を読めなかった |
| storage | 同上。出荷統計は商用調査会社のもので、公開データを見つけていない |
| network | ITU は許諾が必要、TeleGeography のデータは有料、Cloudflare Radar は非営利ライセンス（CC BY-NC 4.0）、IXP の統計は現行規約を見つけられなかった |

この探索は網羅的ではない（IXP の公開統計、各社の決算資料などは未調査）。見つからなかったことは、
存在しないことを意味しない。

## owner 判断が必要なこと（bot は自分で申請しない）

| 項目 | 内容 | 宛先 |
|---|---|---|
| ITU 統計の再利用許諾 | 統計・出版物は許諾の申請が必要 | jur@itu.int |
| SEMI 資料の外部公開許諾 | 派生物の外部公開は個別審査 | mktstats@semi.org |
| WSTS | 許諾なしの複製は禁止 | WSTS（サイトの連絡先） |
| Cloudflare Radar の商用可否 | CC BY-NC 4.0。digest が商用に当たるか判断し、商用なら例外を申請 | Radar about ページの連絡先 |
| 各社決算など出典ごとの確認 | 次の探索の方向 | — |

申請文のドラフトは [`permission-requests.md`](permission-requests.md)（未送信）。

許諾の申請は外部への連絡なので、owner の承認を得てから行う。
