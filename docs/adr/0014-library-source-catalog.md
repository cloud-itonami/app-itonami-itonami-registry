# ADR 0014 Library source catalog (and clj-lib actors)

Status: proposed, 2026-11-17. Builds on ADR 0011 and ADR 0012. Tracked in AWAI-3035, JUN-1070 and AWAI-507.

## Context

108 public, non-fork, non-archived `cloud-itonami` repositories are Clojure/CLJC libraries by file layout
(`deps.edn`, `src/`, `test/`) and carry no `blueprint.edn`, `SOUL.md` or keyed data. hermes-registry has no
library type (skills, mcp, agents, workflows, models). 45 of the 108 describe themselves as actors
(`etzhayyim actor: ... (aozora.app)`, `...-actor`); 63 are libraries, models and `kami-app-*` stubs
("moved from kotoba-lang").

## Decision

1. The 45 actor-described repositories join `catalogs/actors.json` (ADR 0011; 150 -> 195).
2. The 63 others get a **supplemental catalog**, `catalogs/libraries.json`, schema
   `itonami.library-sources.v1`, validated by `validate_libraries`. Same shape as ADR 0012: one pinned 40-hex
   commit, GitHub-reported licence, key `library` (the repository stem) and `sha256` of whichever files of a fixed
   list exist at the pinned commit: `README.md`, `AGENTS.md`, `LICENSE`, `NOTICE`, `MATURITY.md`,
   `manifest.edn`, `deps.edn`, `cljk-origin.edn`, `nbb.edn`. `deps.edn` must be present. No content is copied.
3. `authority: {grants: false, default: "blocked"}` on every entry. Private repositories and forks are skipped.
4. Membership is a reviewed declaration; `scripts/build_library_catalog.py` refreshes, `--add NAME` lists.

## Not decided here

- Moving repositories (for example to `kotoba-lang`) and archiving them. Pinning does not consolidate code.
- Whether libraries should become a registry type with the code inside the registry.
- Licences (27 report none).
