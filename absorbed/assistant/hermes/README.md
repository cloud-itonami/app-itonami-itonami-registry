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
| `bridgetestclone` |  |
| `bridgetestfresh` |  |
| `default` |  |
| `gftd-support` | Email support inbox bot (polling agentmail.to, created 2026-09-02) |
| `kotoba-engineer` | kotoba エンジニア — jv |
| `mithril-coder-openrouter` |  |
| `research` | Reads and summarises: web pages, papers, long documents. Returns findings |
| `review` | Reviews code and designs: finds correctness bugs and simplifications, |
| `theme-designer` | theme design and engineer — dark mode, light mode の design, lib 開発, engineer |
| `writing` | Drafts and edits prose: posts, docs, replies. Keeps the authors voice, |
