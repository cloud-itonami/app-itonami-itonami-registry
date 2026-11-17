# ADR 0012 Blueprint source catalog

Status: proposed, 2026-11-17. Builds on ADR 0004 and ADR 0011. Tracked in AWAI-3029, JUN-1070 and AWAI-507.

## Context

After the keyed datasets (ADR 0004) and actors (ADR 0011) were referenced, 997 non-archived
`cloud-itonami` repositories remained. 413 of the public, non-fork ones carry a `blueprint.edn`
(`:itonami.blueprint/id`, domain, governor, status; the ISIC/ISCO/COFOG ones add a classification
code). They are open business blueprints: a descriptor, a README, a licence and often an
`organization.edn`, `kotoba.app.edn`, `physics.edn` or `facts.edn`, next to source and tests. They have
no `SOUL.md` (not Hermes profiles, ADR 0001) and no dataset key (ADR 0004).

Measured on 2026-11-17 over the 413 repositories' default-branch root trees: `blueprint.edn` 413,
`README.md` 412, `LICENSE` 405, `organization.edn` 224, `kotoba.app.edn` 117, `facts.edn` 21,
`physics.edn` 15. One repository (`app-itonami-oteint`) has a `blueprint.edn` without an
`:itonami.blueprint/id` and is not listed.

## Decision

1. Blueprints get a **supplemental catalog**, `catalogs/blueprints.json`, schema
   `itonami.blueprint-sources.v1` (`schemas/blueprint-sources.schema.json`), validated by
   `validate_blueprints`. It is not in `index.json`; Hermes clients do not read it.
2. An entry is a **reference**: owning repository, one pinned 40-hex commit, licence as reported by
   GitHub, keys (`blueprint` = `:itonami.blueprint/id`; `domain`, `isic`, `isco`, `cofog` when
   `blueprint.edn` declares them), and `sha256` of whichever files of a **fixed list** exist at the
   pinned commit: `blueprint.edn`, `README.md`, `LICENSE`, `organization.edn`, `kotoba.app.edn`,
   `physics.edn`, `facts.edn`. `blueprint.edn` must be present. Source, tests, data and state are never
   listed. No content is copied.
3. Every entry carries `authority: {grants: false, default: "blocked"}`. Listing a blueprint does not
   authorize it to run, call a service or hold a key.
4. **Membership is a reviewed declaration**, not a name pattern. `scripts/build_blueprint_catalog.py`
   refreshes the listed repositories; `--add NAME` lists a new one. Private repositories and forks are
   skipped.
5. Keys are read with a plain text match on `blueprint.edn`; nothing is evaluated.

## Not decided here

- **Retiring repositories.** Publication archives, renames and deregisters nothing. 129 of the listed
  repositories also hold runnable app or physics code (`kotoba.app.edn`, `physics.edn`, `src/`);
  pinning them does not consolidate that code, so archiving them is a separate owner decision.
- **Licences.** Recorded as reported (`NOASSERTION` when none).
- **Private repositories** (78 of the 997) are not described, even by name.

## Consequences

- A consumer can resolve a blueprint to a pinned commit and verify its descriptor without listing the
  organization.
- The catalog is a dated snapshot; re-run the builder and review the diff.
