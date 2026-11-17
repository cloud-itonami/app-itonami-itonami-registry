# ao-repo-steward

`cloud-itonami/ao-repo-steward` — resident bots that keep the workspace repositories tidy.

Git and PR hygiene across the workspace: stale branches and PRs, merges of bot PRs, rule and document currency, cleanup of the superproject. Their subject is the repositories as a whole, not any one of them.

The subject and the bots are one repository: the Hermes profiles that act
here live in [`hermes/profiles/`](hermes/) and are the source of truth for
`~/.hermes/profiles/<profile>` on the host (ADR-2609241200). Secrets, ledgers,
workspace and run state stay on the host.

## Naming

`ao-` is the role prefix for a repository that is a resident bot (the
kotoba-lang/ao artificial-organism model) whose subject and Hermes profile
live together. Identity is the path `cloud-itonami/ao-repo-steward`.

## Profiles

| profile | role |
|---|---|
| `90-docs` | — |
| `awai-store-removal` | network-awai D1/DO/KV binding removal driver (ADR-2609132007): one repo per tick, read source, migrate to R2, verify, PR + merge. propose-on |
| `branch-drain` | — |
| `cljk-finish` | cljk-finish - finish the clj/cljc/cljs to cljk rename follow-through (string-literal |
| `design-audit` | デザイン/アクセシビリティ監査担当。itonami.cloud と workspace 配下の web UI を |
| `docs-audit` | docs-currency audit bot: checks shared read-only models, rules, md, |
| `git-cleanup-ops` | git-cleanup-ops — ローカル側 cleanup の定期出口（daily 05:10 JST） |
| `kotoba-merger` | kotoba-merger — org-wide PR review & merge bot |
| `pr-cleanup` | pr-cleanup — github pr を cleanup |
| `pr-drain` | — |
| `reviewer` | reviewer |
| `rule-kaizen` | rule-kaizen bot: standing な言い方が実装スナップショットを言語にしていないか測り、1 反復 1 finding で直す (ADR-2608261200), 3h cron |
| `seiri` | cleanup・整理整頓専任。superproject と各 repo の cleanup(cleanup.cljs/cleanup-land.cljs)、west |
