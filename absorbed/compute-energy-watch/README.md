# app-itonami-compute-energy-watch

世界の電力・CPU・network・storage・GPU の生産/供給・需要・消費を、公開出典だけから
出典付きで分析する itonami dapp（`app-itonami-*`）。bot profile を同梱する（1 profile 1 repo、registry ADR 0008）。
旧名 `cloud-itonami/compute-energy-watch`（2026-10-28 に改名、GitHub が旧 URL を転送する）。

- profile: `hermes/profiles/compute-energy-watch/`
- 設計: [`docs/design.md`](docs/design.md)
- 追跡: Linear JUN-495

状態: profile 定義のみ。dapp の UI・状態は未実装（実装時は workspace の「Kotoba end-user apps run in the user's environment」契約に従い、静的配信とブラウザ実行にする）。データ源の権利は未確認、ランタイムは未検証。cron は無効。
