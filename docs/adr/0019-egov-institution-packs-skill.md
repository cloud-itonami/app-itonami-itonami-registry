# ADR 0019 E-government institution packs as a knowledge skill

Status: proposed, 2026-11-18. Builds on ADR 0016 and ADR 0018. Tracked in AWAI-3421 (parent AWAI-155, AWAI-3147).

## Context

The municipality archive (ADR 0018) is an index of local rules, not procedures. The procedures an assistant can state with
a primary source live in the institution packs (`seido/*.edn`) of `network-awai/app-itonami-egov`, which the Shakai,
Kaisha and Matsuri profiles (registered here since AWAI-3147) and the Gyosei screen of the Itonami app evaluate. Owner
direction (2026-11-18): government procedures go into the Shakai screen for the user, and the capability itself is also
placed in the registry.

## Decision

1. `skills/knowledge/egov-seido-packs`: `SKILL.md`, `references/index.json` (pack id, jurisdiction, version, review state,
   dates, procedure ids, subdivisions with their fixture flag) and `references/seido/*.edn` copied verbatim from git
   objects at the pinned commit. One source entry in `catalogs/sources.json` with the sha256 of each file; the
   registration goes on the repository's row in `catalogs/targeted-public-sources.json`. Builder:
   `scripts/build_egov_seido_skill.py --checkout <app-itonami-egov> --commit <sha>`.
2. `workflow/municipal-procedure-guide` also uses the skill in its lookup step: local rules from the municipality archive,
   national procedures from the pack when one exists.
3. The egov profile pins are not moved when their files are unchanged. At `bf8253f` they are identical to the
   registered `10259965`.

## Not decided here

- Expert review of the packs. They stay `:unreviewed`, so no submission is proposed.
- Packs for the other countries in the municipality archive. Each needs a fetched primary source; the ordinance index
  alone does not produce a procedure.
