# ADR 0015 App source catalog (and the last actor-described repositories)

Status: proposed, 2026-11-17. Builds on ADR 0011, ADR 0012 and ADR 0014. Tracked in AWAI-3048, JUN-1070 and AWAI-507.

## Context

On 2026-11-17, after the dataset, actor, blueprint and library catalogs, 981 non-archived `cloud-itonami`
repositories remained; 588 were already referenced. Of the other 393, 320 are public non-forks with no
catalog: runnable apps and Workers (`package.json`, `shadow-cljs.edn`, `wrangler.*`, `kotoba.app.edn`),
Clojure applications, and small stubs. 38 of them describe themselves as actors. The 73 private repositories
are not described, even by name.

## Decision

1. The 38 actor-described repositories join `catalogs/actors.json` (ADR 0011).
2. The other 282 get a **supplemental catalog**, `catalogs/apps.json`, schema `itonami.app-sources.v1`,
   validated by `validate_apps`. Same shape as ADR 0012/0014: one pinned 40-hex commit, GitHub-reported
   licence, key `app` (the repository stem), `kind` derived from which listed files exist (`worker-app` if a
   `wrangler.*` exists, else `kotoba-app` for `kotoba.app.edn`, else `js-app` for `package.json` or
   `shadow-cljs.edn`, else `clj-app` for `deps.edn`, else `other`) and `sha256` of whichever files of a fixed
   list exist: `README.md`, `AGENTS.md`, `LICENSE`, `NOTICE`, `MATURITY.md`, `manifest.edn`, `kotoba.app.edn`,
   `package.json`, `wrangler.jsonc`, `wrangler.toml`, `shadow-cljs.edn`, `deps.edn`, `nbb.edn`,
   `cljk-origin.edn`. `digestStatus` is `unverified` for a repository with none of them. No content is copied.
3. `authority: {grants: false, default: "blocked"}`. Private repositories and forks are skipped.
4. Membership is a reviewed declaration; `scripts/build_app_catalog.py` refreshes, `--add NAME` lists.

## Not decided here

- Archiving. Pinning does not consolidate code; these repositories are live sources.
- Which apps move to `network-awai` as Awai apps (Tauri hosts exist for 19 of them, already moved) and which
  stay: that follows the Tauri qualification (AWAI-509), not this catalog.
- Licences, and the 73 private repositories.

## Consequences

- Every public non-archived `cloud-itonami` repository is referenced by exactly one catalog (dataset,
  actor, blueprint, library or app) or is a registry/profile owner; the registry can be refreshed from it.
