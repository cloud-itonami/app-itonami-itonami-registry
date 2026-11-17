# ao-hiraku

`cloud-itonami/ao-hiraku` — 情報格差を埋め、子ども・若者の可能性を kotoba で「ひらく」常駐 bot 群。

性別・地域・年齢・文化（言語・ルーツ）・障害・経済・家庭環境によって、
「知っていれば使えた制度」「知っていれば選べた進路」に届かない人がいる。
この repo は、その差を **情報が届く経路をつくること** で埋める bot と、その bot が使うデータ
（道しるべカタログ・教材カリキュラム）を一緒に持つ。

The subject and the bots are one repository: the Hermes profiles that act
here live in [`hermes/profiles/`](hermes/) and are the source of truth for
`~/.hermes/profiles/<profile>` on the host (ADR-2609241200). Secrets, ledgers,
workspace and run state stay on the host.

プロセス設計の正本は [`docs/empowerment-process.md`](docs/empowerment-process.md)。

## Profiles

| profile | role | 動き方 |
|---|---|---|
| `hiraku-michishirube` | 道しるべ — 格差軸 × 年代のマトリクスで無料・公的リソースのカタログを保守。最も薄いセルに 1 件の追加を提案 | cron 1日1回, propose-only |
| `hiraku-kyozai` | 教材 — やさしい日本語・多言語・年代別の学習教材を kotoba LLM で 1 本ずつ起こし、品質ゲートを通す | cron 1日2回, draft → gate → ready（公開は人間） |
| `hiraku-soudan` | 相談 — 本人・保護者・先生からの相談に、カタログを根拠に「次の一歩」を返す対話 bot | chat（`hermes -p hiraku-soudan chat`）。外部チャネル接続は operator 判断 |

## Data

| file | 中身 |
|---|---|
| [`data/axes.json`](data/axes.json) | 格差の軸（gender / region / age / culture / disability / economy / family）と年代ステージ |
| [`data/catalog.json`](data/catalog.json) | 道しるべカタログ。1 エントリ = 1 つの無料・公的リソース。`verified` は michishirube の URL 実測で更新 |
| [`data/curriculum.json`](data/curriculum.json) | 教材のテーマ × 年代 × 言語のローテーション定義 |
| [`data/safety.json`](data/safety.json) | 緊急時の相談窓口（全 bot が必ず案内する固定リスト）と、出力に含めてはいけない表現 |

## 実行基盤

3 profile とも **itonami-agent**（[kotoba-lang/itonami-agent](https://github.com/kotoba-lang/itonami-agent)）が cron を回す（`profile adopt` 済み、Hermes 側は `gateway.parked` で停止）。
常駐: `~/Library/LaunchAgents/cloud.itonami.agent.gateway.plist`。配置は `[:peer :local]`（信頼済みピアがあればピア、無ければローカル）。
Hermes に戻すときは `itonami-agent profile release <profile>`。

## LLM

Approved Itonami Hermes profiles use the locally hosted Mishima inference fleet through the Murakumo endpoint. Their effective configuration is `provider: murakumo`, `default: mishima`, and an empty `fallback_providers` list. OpenRouter, `murakumo/free`, Kotoba inference, and peer inference are not active fallback targets. Sending profile or session context to a nonlocal peer requires separate explicit owner approval.

Cron jobs are currently run by `itonami-agent`; the Hermes gateway is parked. Saving a Hermes profile does not show that a job is registered or running.

## Naming

`ao-` is the role prefix for a repository that is a resident bot (the
kotoba-lang/ao artificial-organism model) whose subject and Hermes profile
live together. `hiraku`（ひらく）は「可能性をひらく」「扉をひらく」から。
