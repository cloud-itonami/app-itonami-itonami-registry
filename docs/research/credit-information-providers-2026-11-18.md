# 企業信用情報 3 社の規約・API・契約条件と操作宣言の案（2026-11-18）

Linear: AWAI-3187（親 AWAI-3186）。確認日はすべて 2026-11-18（日本時間）。

この文書は、DUNS（Dun & Bradstreet）・帝国データバンク（TDB）・Moody's を扱う Itonami profile を作る前の調査記録です。法的助言ではありません。各社の契約書・注文書（Order Form）は非公開なので、公開資料から分かる範囲だけを書き、分からない項目は `unknown` としています。

## 結論

- 3 社とも、データの取得には個別の有償契約が要ります。公開の無償 API はありません。
- 3 社とも、サイトの自動取得（bot・scraping）、無断の再配布、データの複製を禁じています。Moody's はさらに、AI の学習に使うことも明文で禁じています。
- そのため、この profile は**利用者が自分で結んだ契約の資格情報**を使い、利用者の端末から各社へ直接接続する形にします。Awai や Itonami が一括で契約して再販する形は取りません。また、取得したデータを registry や公開 corpus に複製しません。
- API の仕様が公開されているのは D&B Direct+ だけです。TDB は秘密保持契約（NDA）を結んだ後に仕様書が開示されます。Moody's Orbis は契約者向けに文書が提供されます。そのため、TDB と Moody's の endpoint は `unknown` のままです。
- 日本企業の D-U-N-S 番号は、D&B の日本での提携先である東京商工リサーチ（TSR）が発番・照会しています。TSR の窓口は Web のフォームだけで、API は公開されていません。

## 1. Dun & Bradstreet（D-U-N-S）

### 1.1 D&B Direct+ API

| 項目 | 内容 | 出典 |
|---|---|---|
| 認証 | OAuth 2 Client Credentials。`POST https://plus.dnb.com/v1/token` に `Authorization: Basic base64(key:secret)` と `{"grant_type":"client_credentials"}` を送る | [D&B Direct+ Authentication](https://docs.dnb.com/partner/en-US/plus/token/1.0/authentication) |
| トークン | 有効期限は 24 時間（`expiresIn: 86400`）。以後の要求は `Authorization: Bearer <token>` を付ける。期限切れはエラー `00040` | 同上 |
| 資格情報の入手 | 「D&B の担当者に連絡して key/secret を入手する」。セルフサービスでの発行はない | 同上 |
| API の origin | `https://plus.dnb.com` | 同上 |
| 主な操作 | 照合（`/v1/match/cleanseMatch`。DUNS・登記番号・名称と住所・電話・URL・メールで照合）、DUNS 指定のデータ取得（`/v1/data/duns/{duns}`。商品 ID と版を指定）、社名の前方一致検索（Search API の typeahead） | [Using the D&B Direct+ APIs](https://directplus.documentation.dnb.com/html/pages/UsingDplusAPIs.html)、[Feature Introduction](https://directplus.documentation.dnb.com/html/pages/DplusIntroduction.html)、[Search APIs](https://directplus.documentation.dnb.com/html/pages/SearchAPIs.html) |
| ドキュメントの公開範囲 | `directplus.documentation.dnb.com` の詳細ページは D&B の SSO へ転送されるため、今回は本文を読めていない。上の操作名とパスは検索結果の要約から取ったもの。正確なクエリ名は契約後に確認する | 2026-11-18 に取得を試行 |
| sandbox | `unknown`（公開資料に記載がない） | — |
| 料金 | `unknown`（非公開。契約ごと） | — |
| ブラウザからの直接接続（CORS） | `unknown`。トークン要求の例に `Origin: www.dnb.com` があり、ブラウザからの直接呼び出しを想定していない可能性がある | 上記 Authentication |

### 1.2 dnb.com サイトの利用規約

- サイトの内容を体系的に取得・抽出することを禁止し、bot・spider を名指ししている。
- 書面の同意なく第三者に共有すること、サービスを使ってデータベースを作ることを禁止している。
- 商品（Direct+ など）の利用条件は、Master Agreement・Product License Agreement・Order といった別の契約で定める。
- AI・機械学習についての記載はない（`unknown`）。

出典: [Dun & Bradstreet Terms of Use](https://www.dnb.com/utility-pages/terms-of-use.html)（ページに改定日の表示なし）

### 1.3 日本企業の D-U-N-S 番号（東京商工リサーチ）

窓口は [D-U-N-S Number 検索サイト](https://duns.tsr-net.co.jp/duns-web/index) で、Web のフォームから申し込みます。API は公開されていません。2025-11-14 に料金が改定されています（税別）。

| サービス | 納期 | 料金 |
|---|---|---|
| 自社番号の照会 | 即時 | 10,000 円/件 |
| 自社番号の発番 | 7 営業日 | 15,000 円/件（30 営業日を選ぶと無償。簡易な通知書での納品） |
| 自社の登録情報の変更 | 7 営業日 | 無償 |
| 他社番号の照会 | 即時 | 10,000 円/件 |
| 他社番号の発番 | 7 営業日 | 15,000 円/件 |

出典: [TSR お知らせ「D-U-N-S Number 検索サービス 料金改定」（2025-11-10 発表）](https://www.tsr-net.co.jp/release/detail/1201991_1522.html)。Apple・FDA・UPIK 向けの専用ページから申し込むと、無償かつ短納期で取得できるとの案内もある（同社のお知らせ）。

関連する規約として、[D&B D-U-N-S Registered 利用約款](https://www.tsr-net.co.jp/terms/3dunsnumber.pdf)（2024-04-01 改定）がある。これは D-U-N-S Registered（認証シールとプロファイル掲載）の約款で、照会・発番そのものの約款ではない。第 14 条の禁止事項には、TSR・D&B が正確性を保証しているかのような表明、シールの改変、システムへの不正アクセスなどが並ぶ。

## 2. 帝国データバンク（COSMOSNET API）

| 項目 | 内容 | 出典 |
|---|---|---|
| 提供情報 | 基本情報（商号・所在地など）、概要情報（売上高・利益・株主・取引先・評点など）、調査報告書、財務情報（貸借対照表・損益計算書など） | [COSMOSNET API サービス](https://www.tdb.co.jp/services/lineup/api/) |
| 取得方法 | 利用者のシステムから TDB のデータベースを検索し、リアルタイムに取得する | 同上 |
| 契約 | 個別の見積と契約が必要。API 仕様書は秘密保持契約を結んだ後に開示される。利用案内への同意が前提 | 同上 |
| 認証 | 「お客さまの APIID を使用して API でなされた行為」について利用者が責任を負う、とある。具体的な認証方式は `unknown` | 同上 |
| テスト環境 | 本番前にテスト環境を使う場合も利用案内への同意が必要、とある。内容は `unknown` | 同上 |
| 料金 | 個別見積（`unknown`） | 同上 |
| 稼働 | ベストエフォート。計画停止・緊急停止がありうる | 同上 |
| 再配布・二次利用・AI 利用 | 公開ページに記載なし（`unknown`）。利用案内と契約で定めると考えられる | 同上 |
| endpoint の origin とパス | `unknown`（NDA の後に開示） | 同上 |

他社製品との連携として、kintone プラグインと UiPath コネクタがある。どちらも部品自体は無償だが、別途 TDB とのデータ契約が要る（[UiPath 発表 2020-03-10](https://www.uipath.com/ja/newsroom/connector-for-tdb-2020-3-10)、[kintone プラグイン](https://kintone-sol.cybozu.co.jp/integrate/tdb001.html)、[TDB データ連携サービス](https://www.tdb.co.jp/services/details/datalinkage/)）。

## 3. Moody's

### 3.1 Orbis（旧 Bureau van Dijk の企業データベース）

| 項目 | 内容 | 出典 |
|---|---|---|
| 利用許諾の範囲 | 限定的・非独占・譲渡不可の利用許諾。使ってよいのは、契約・Order Form・Orbis T&C が明示的に認める目的だけ | [Orbis Content Terms and Conditions](https://www.moodys.com/web/en/us/legal/orbis-content-terms-and-conditions.html)（2024-11-14 更新） |
| 保存・ダウンロード | 認められた目的に必要な「限られた抜粋」のみ。全体や大部分を得るための取得・複製は、1 回でも複数回でも禁止 | 同上 |
| 競合製品 | Moody's や提供元と競合する製品、または実質的に同様の内容・機能を持つ製品を作ることを禁止 | 同上 |
| 再配布・自動取得・AI 利用 | この文書には記載なし（`unknown`）。Order Form で定めると考えられる | 同上 |
| API の endpoint・認証 | `unknown`。公開の開発者文書は見つからなかった。契約者には文書と試用の資格情報が提供される、との第三者の記載がある | 2026-11-18 の検索 |

### 3.2 格付（Moody's Ratings）

- `ratings.moodys.com` の閲覧は無償だが、アカウント登録が必要。コピーできるのは社内業務の目的に限られる（Terms of Use 1(a)）。
- 自動のプログラムやツール（bot・spider）でサイトにアクセスすることを禁止している（1(c)(iv)）。scraping やデータマイニングには事前の書面同意が要る（1(c)(ii)、2）。
- サイトや資料（格付を含む）を使って、ソフトウェアやデータベースを開発・改良・学習・再学習することを禁止している。AI・機械学習・自然言語処理のモデルも明記されている（1(c)(iii)）。
- 加工・再パッケージ・販売・再配布には事前の書面同意が要る（1(c)(ii)）。

出典: [Moody's Terms of Use](https://www.moodys.com/web/en/us/legal/terms-of-use.html)（2024-10-21 更新）

格付データをまとめて受け取る手段には、DataHub（クラウド・SFTP・直接ダウンロード）や Ratings Delivery Service があり、いずれも有償の契約が前提です（[Moody's DataHub](https://www.moodys.com/web/en/us/datahub.html)）。API の仕様は公開されていません（`unknown`）。

## 4. profile の設計への影響

1. **資格情報は利用者のもの**: D&B の key/secret、TDB の APIID、Moody's の資格情報は、利用者の端末にだけ保存します。profile・bot・registry に入れません（registry ADR 0003）。
2. **自動巡回をしない**: `ratings.moodys.com`、`dnb.com`、TSR の検索サイトを bot が自動で開いたり取得したりすることはしません。契約 API がない操作は「公式ページを利用者が自分で開く」案内にとどめます。
3. **取得データを複製しない**: 照会結果は利用者の手元の状態にだけ置きます。registry・Awai FS の公開領域・学習用 corpus に入れません。
4. **推論に渡すときの扱い**: 取得データを要約などのために推論 rail（murakumo / mishima）へ送ることが、各社の契約で許されるかは `unknown` です。確認できるまでは端末内の推論だけを使い、遠隔の推論に送る場合は操作ごとに別の同意を取ります。Moody's については、学習に使わないことを明記します。
5. **課金が発生する操作**: TSR の照会・発番や、TDB の調査報告書など課金が発生する操作は、購入として扱います。金額と内容を示して毎回確認し、bot が自動では実行しません。

## 5. 操作宣言の案（`kotoba.app.client-runtime.v1`）

D&B Direct+ のうち、パスが公開資料で確認できたものだけを宣言します。TDB と Moody's は endpoint が `unknown` なので、宣言の雛形だけを置きます。共有 broker は未宣言の endpoint を拒否するので、雛形のままでは要求は送られません。

```json
{
  "operations": [
    {
      "capability": "credit-info",
      "service": "dnb-direct-plus",
      "operation": "token",
      "consent": "each-operation",
      "data-categories": ["service-credential"],
      "endpoint": {
        "origin": "https://plus.dnb.com",
        "routes": [{"method": "POST", "path": "/v1/token", "query-params": []}]
      }
    },
    {
      "capability": "credit-info",
      "service": "dnb-direct-plus",
      "operation": "match-company",
      "consent": "each-operation",
      "data-categories": ["company-identifiers", "company-name-and-address", "service-credential"],
      "endpoint": {
        "origin": "https://plus.dnb.com",
        "routes": [{"method": "GET", "path": "/v1/match/cleanseMatch", "query-params": "unknown: 契約後に D&B の文書で確定"}]
      }
    },
    {
      "capability": "credit-info",
      "service": "dnb-direct-plus",
      "operation": "get-company-by-duns",
      "consent": "each-operation",
      "data-categories": ["company-identifiers", "service-credential"],
      "endpoint": {
        "origin": "https://plus.dnb.com",
        "routes": [{"method": "GET", "path-prefix": "/v1/data/duns/", "query-params": ["productId", "versionId"]}]
      }
    },
    {
      "capability": "credit-info",
      "service": "tdb-cosmosnet-api",
      "operation": "search-and-get-company",
      "consent": "each-operation",
      "data-categories": ["company-identifiers", "company-name-and-address", "service-credential"],
      "endpoint": "unknown: NDA の後に開示される仕様書で確定"
    },
    {
      "capability": "credit-info",
      "service": "moodys-orbis",
      "operation": "search-and-get-company",
      "consent": "each-operation",
      "data-categories": ["company-identifiers", "company-name-and-address", "service-credential"],
      "endpoint": "unknown: 契約者向け文書で確定"
    }
  ]
}
```

注意:

- route のキー名（`path`・`path-prefix`・`query-params`）は、awai-os に vendored された共有 broker（`otehon/shell/vendor-dougaka/kotoba-client-runtime.js`）が使う名前に合わせました。`unknown` の値は宣言として無効なので、確定するまで broker はこの操作を受け付けません。
- typeahead 検索は、パスを一次資料で確認できていないので宣言に入れていません。
- D&B がブラウザからの直接接続（CORS）を許すかは `unknown` です。許さない場合でも、app origin を proxy にはしません（共有アーキテクチャ契約）。端末側の HTTP（Tauri）を共有 broker 経由で使う形を、AWAI-3189 で検討します。
- TSR の D-U-N-S 照会・発番と、Moody's の格付閲覧は、API がないかサイトの自動取得が禁止されているため、宣言に入れません。

## 6. owner の判断が要る項目

1. **契約の形**: 利用者がそれぞれ自分で契約する前提でよいか。Awai や Itonami が一括で契約して提供する形は、3 社の再配布の制限に当たる可能性が高い。
2. **D&B の契約窓口**: 日本の利用者向けに、D&B Direct+ を D&B と直接契約するか、TSR の商品を使うか。
3. **開発用の資格情報**: profile の動作確認（AWAI-3188）に使う sandbox や試用の資格情報を、どの契約で得るか。TDB は見積と NDA、Moody's は試用の申し込みが要る。取れない場合は、架空データの stub だけで確認する。
4. **推論への送信**: 取得データを遠隔の推論（murakumo / mishima）に送ってよいかを、各社の契約で確認する。

## 7. 未確認（`unknown`）の一覧

- D&B Direct+: sandbox の有無、料金、CORS、cleanseMatch と typeahead の正確なクエリ名、AI 利用の条件
- TDB: endpoint、認証方式、テスト環境の内容、料金、再配布・二次利用・AI 利用の条件
- Moody's: Orbis と格付 API の endpoint・認証、料金、Orbis の再配布・自動取得・AI 利用の条件（Order Form 側）
