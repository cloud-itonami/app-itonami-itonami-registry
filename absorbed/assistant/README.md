# ao-assistant

`cloud-itonami/ao-assistant` — general-purpose and scratch hermes profiles.

Profiles that serve a person directly (research, review, writing) and scratch or test profiles kept for the harness. They hold no standing duty on a product.

The subject and the bots are one repository: the Hermes profiles that act
here live in [`hermes/profiles/`](hermes/) and are the source of truth for
`~/.hermes/profiles/<profile>` on the host (ADR-2609241200). Secrets, ledgers,
workspace and run state stay on the host.

## Naming

`ao-` is the role prefix for a repository that is a resident bot (the
kotoba-lang/ao artificial-organism model) whose subject and Hermes profile
live together. Identity is the path `cloud-itonami/ao-assistant`.

## Profiles

| profile | role |
|---|---|
| `bridgetestclone` | — |
| `bridgetestfresh` | — |
| `default` | — |
| `gftd-support` | Email support inbox bot (polling agentmail.to, created 2026-09-02) |
| `kotoba-engineer` | kotoba エンジニア — jv |
| `mithril-coder-openrouter` | — |
| `research` | Reads and summarises: web pages, papers, long documents. Returns findings |
| `review` | Reviews code and designs: finds correctness bugs and simplifications, |
| `theme-designer` | theme design and engineer — dark mode, light mode の design, lib 開発, engineer |
| `writing` | Drafts and edits prose: posts, docs, replies. Keeps the authors voice, |
