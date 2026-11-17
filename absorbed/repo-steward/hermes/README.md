# hermes/ — the resident bots that act for this repository

This directory is the **source of truth** for the Hermes profiles listed below
(ADR-2609241200). The host's `~/.hermes/profiles/<profile>` is materialized
from `hermes/profiles/<profile>/` and checked against it:

```
kbb --backend sci scripts/hermes-profile-repo.cljk materialize <profile>   # repo -> host
kbb --backend sci scripts/hermes-profile-repo.cljk check <profile>         # 0 agree / 1 drift / 2 could not compare
kbb --backend sci scripts/hermes-profile-repo.cljk export <profile>        # host -> repo, then commit
```

(run from the com-junkawasaki/root superproject; registry
`manifest/hermes-profile-repos.edn`.)

Each profile directory holds SOUL.md, profile.yaml, config.yaml (host-local
blocks removed), cron/jobs.json (definitions only), scripts/ and the skills the
profile owns. **Never here:** `.env` or any secret value, workspace/ledgers,
sessions, memories, logs, caches, run state.

## Profiles

| profile | description |
|---|---|
| `90-docs` |  |
| `awai-store-removal` | network-awai D1/DO/KV binding removal driver (ADR-2609132007): one repo per tick, read source, migrate to R2, verify, PR + merge. propose-only for deploy. |
| `branch-drain` |  |
| `cljk-finish` | cljk-finish - finish the clj/cljc/cljs to cljk rename follow-through (string-literal |
| `design-audit` | デザイン/アクセシビリティ監査担当。itonami.cloud と workspace 配下の web UI を |
| `docs-audit` | docs-currency audit bot: checks shared read-only models, rules, md, |
| `git-cleanup-ops` |  |
| `kotoba-merger` |  |
| `pr-cleanup` | pr-cleanup — github pr を cleanup |
| `pr-drain` |  |
| `reviewer` |  |
| `rule-kaizen` | rule-kaizen bot: standing な言い方が実装スナップショットを言語にしていないか測り、1 反復 1 finding で直す (ADR-2608261200), 3h cron |
| `seiri` | cleanup・整理整頓専任。superproject と各 repo の cleanup(cleanup.cljs/cleanup-land.cljs)、west |
