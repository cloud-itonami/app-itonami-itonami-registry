# ADR 0011 Actor source catalog

Status: proposed, 2026-11-17. Builds on ADR 0001, ADR 0004 and ADR 0008. Tracked in JUN-1070 and AWAI-507.

## Context

The organization holds repositories that are neither Hermes profiles nor keyed data: executable,
governed Kotoba **actors** (`etzhayyim actor: <name> (aozora.app)`, `actor-*`, persona-driven loop
actors). On 2026-11-17, 104 non-archived repositories matched this role and had no registry
reference. They have no `SOUL.md`, so `scripts/add_profile.py` cannot register them, and ADR 0001
forbids a fifth Hermes manifest type. They are not datasets, so ADR 0004's keys do not fit.

Measured over those 104 repositories (default-branch file trees; the identity-file counts cover all 104, the DID and license counts cover the 83 eligible):

- 83 are public and not forks; 21 are private or forks. Only the 83 are eligible.
- Identity is spread over several optional files: `README.md` (92), `AGENTS.md` (69),
  `manifest.edn` (54), `repository-contracts.edn` (44), `identity.edn` (31), `did.json` (57),
  `MATURITY.md` (28), `kotoba.app.edn` (23), `actor.edn` (19). No single file is universal.
- 45 of the 83 carry a `did:web:` identifier in a declared file.
- 75 of the 83 report no license (`NOASSERTION`).
- Some repositories are moves of a canonical repository elsewhere (for example `actor-bunken`
  names `kotoba-lang/actor-bunken` as canonical) and keep a compatibility identity.

## Decision

1. Actors get a **supplemental catalog**, `catalogs/actors.json`, schema `itonami.actor-sources.v1`
   (`schemas/actor-sources.schema.json`), validated by `validate_actors`. It is not in `index.json`
   and Hermes clients do not read it.
2. An entry is a **reference**: owning repository, one pinned 40-hex commit, license as reported by
   GitHub, `kind` (`actor` or `persona-loop`), keys (`actor`, and `did` when a declared file carries a
   `did:web:` identifier), and `sha256` of whichever files of a **fixed list** exist at the pinned
   commit. No content is copied.
3. The fixed list is `README.md`, `AGENTS.md`, `manifest.edn`, `identity.edn`, `actor.edn`,
   `kotoba.app.edn`, `did.json`, `MATURITY.md`, `repository-contracts.edn`. Source code, data, lexicons
   and any state are never listed. `digestStatus` is `verified` only when the payload is non-empty and
   every digest was computed from the pinned commit.
4. Every entry carries `authority: {grants: false, default: "blocked"}`. Listing an actor does not
   authorize it to run, call a service or hold a key. Actor runtime and consent follow the Kotoba
   shared contract, not this catalog.
5. **Membership is a reviewed declaration.** It is the list of entries in the file, not a name
   pattern. `scripts/build_actor_catalog.py` refreshes the repositories already listed; `--add NAME`
   lists a new one. Private repositories and forks are skipped, never listed.
6. One repository is one entry, even when several repositories describe the same actor (for example
   `business-person` and `business-person-actor`). The catalog does not merge or pick a canonical one;
   `keys.actor` makes the overlap visible.

## Not decided here

- **Retiring repositories.** Like ADR 0004, publication archives, renames and deregisters nothing.
  Archiving follows the same gate used for the keyed families: pin equals default HEAD, digests
  verified at HEAD, public, no open PR, and each consumer already resolves by pinned commit.
- **Canonical versus moved repositories.** Whether the `cloud-itonami` copy or the
  `kotoba-lang/actor-*` copy is canonical is an owner decision per actor.
- **Licenses.** 75 entries report no license. The catalog records `NOASSERTION` honestly and does not
  imply reuse rights. Adding licenses is the owning repository's change.
- **Promotion to profiles.** An actor that gains a `SOUL.md` profile may move to ADR 0002 and leave
  this catalog; that is a per-actor change.
- **Private repositories.** The 21 non-public repositories are not described, even by name, in the
  catalog.

## Consequences

- A consumer can resolve an actor to a pinned commit and verify its identity files without listing the
  organization.
- The catalog is a dated snapshot. A stale commit means "as observed"; re-run the builder and review
  the diff.
- The 83 eligible repositories become registry-referenced, which unblocks archiving them once the gate
  above holds.
