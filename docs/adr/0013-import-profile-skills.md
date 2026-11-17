# ADR 0013 Import of skills that live inside profile repositories

Status: proposed, 2026-11-17. Builds on ADR 0002, ADR 0008 and ADR 0010. Tracked in AWAI-3034, JUN-1070 and AWAI-507.

## Context

Owner decision (2026-11-17, AWAI-507): move substance into the registry where it fits the
hermes-registry layout (self-contained `skills/`, `agents/`, `workflows/`); what does not fit goes to
awai.network. cloud-itonami content is AGPL-3.0-or-later.

A recursive scan of the 919 public non-archived `cloud-itonami` repositories found 313 `SKILL.md`, 197
profile `SOUL.md` and 15 `AGENT.md`. The 15 `AGENT.md` are the registry's own `agents/`. The 197 `SOUL.md`
are Hermes profiles, whose substance follows ADR 0010 (AwaiFS, pointers in the registry). 312 of the
313 `SKILL.md` sit under profile `skills/` directories: 81 distinct contents under 37 names (for example
`git-cleanup-conflict` has 4 variants over 13 repositories). None of the 37 names existed in `skills/`.

## Decision

1. Each skill name becomes one registry skill, `skills/<category>/<name>/`, copied from a pinned default-branch
   commit of an owning repository: `SKILL.md` plus the files bundled in its folder (nested skill folders are
   separate skills; files over 256 KiB, symlinks and non-regular files are skipped).
2. **Canonical variant = the variant used by the most repositories** (owner decision 2026-11-17); ties go to the
   lexicographically first repository.
3. `SKILL.md` gains `metadata.hermes` (version, author, source pin, compatibility) and `license:
   AGPL-3.0-or-later`; the body and bundled files are unchanged. Private network addresses are redacted.
4. Provenance: `catalogs/sources.json` pins every copied file by sha256 of the original bytes (source ids
   `skillimport-<repo>-<commit8>`), `catalogs/inventory.json` records the registration, and an `itonami.json`
   sidecar is written with `authority.grants: false`, `effects: ["unreviewed"]` and `validation.live: false`.
5. Skills with no frontmatter `description` are skipped, not invented.
6. Categories are assigned by name (`software-development`, `research`, `devops`, default `operations`).
7. The importer is `scripts/import_profile_skills.py`; it executes nothing from the source.

## Not decided here

- Effects, avoid-when and inputs/outputs of each skill are unreviewed.
- Older profile-bundled copies stay in their repositories; profiles are not rewritten to point at the registry skill.
- Archiving the source repositories (they still own profiles, apps and state).
- The 2 skipped skills (`fleet-watchdog-ops`, `wellbecoming-replication`) and `ui-review`'s `agent/SKILL.md`.

## Consequences

- 35 skills become installable from the registry without resolving a profile.
- Variants other than the canonical one are not represented; the differences are in the owning repositories.
- Imported text is operational prose written for internal runs and may carry historical measurements.
