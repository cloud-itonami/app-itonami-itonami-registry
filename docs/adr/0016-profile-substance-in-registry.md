# ADR 0016 Profile substance kept in the registry (seven profile-only repositories)

Status: proposed, 2026-11-17 (extended the same day to app-itonami-cloud-itonami-carrier and app-itonami-animeka-actor, AWAI-3068). Amends ADR 0002 (the registry never copies profile files) and ADR 0010
(substance on AwaiFS) for the profiles below only. Tracked in AWAI-3066, JUN-1070 and AWAI-507.

## Context

Owner decision (2026-11-17, AWAI-507): move the substance into the registry and delete the owning
repositories for `app-itonami-assistant`, `-amano-dns`, `-bot-fleet`, `-compute-energy-watch`, `-hiraku`,
`-repo-steward` and `-social-capital`. These repositories hold only Hermes profiles (`hermes/profiles/*`),
a README and a few documents. ADR 0002 pins a profile in its owning repository; deleting the repository
would leave every pin dangling.

## Decision

1. A profile entry may declare `profile.storage: "registry"`. Its pinned files are then also kept verbatim
   in `profiles/<id>/substance/<path>`. `validate.py` requires that file list and each sha256 to equal the
   manifest's, exactly; `repository`, `commit` and `checksum` stay as the origin record.
2. Profiles whose pin was behind the repository's default branch were re-pinned to it first
   (`bot-fleet` 9, `repo-steward` 13, `social-capital` 1 profiles) with `scripts/add_profile.py`.
3. Files outside `hermes/profiles/` (README, documents, `hiraku` data, tests) are copied verbatim to
   `absorbed/<repo>/…` with an `ABSORBED.json` of digests, checked by `validate_absorbed`.
4. Runtime state is not absorbed: `social-capital`'s `workspace/social-capital-evidence.jsonl`
   (409 bytes, an evidence log) is kept as evidence outside the registry; `.jsonl`, `.db` and `.sqlite` stay
   refused by `validate.py`.
5. `accountability-steward` exists in `bot-fleet` but is registered from `kotoba-lang/kotoba`; that
   registration is left as is.
6. The ADR 0002 `sourceRefs`, `catalogs/sources.json` and inventory registrations keep pointing at the
   origin commits as provenance; after the repositories are deleted those URLs no longer resolve.

## Not decided here

- Whether other profiles move the same way (ADR 0010 remains the default).
- Deleting the repositories: a separate, irreversible step that needs its own confirmation.

## Consequences

- 38 profiles and the absorbed files no longer depend on their repositories.
- The registry now holds profile instructions (SOUL.md, config.yaml, cron jobs, skills); cron arrives
  disabled and accounts, grants and secrets are still rebound by the installer (ADR 0002).
