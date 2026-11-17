# ADR 0018 Municipality archives as a knowledge skill and a procedure workflow

Status: proposed, 2026-11-17. Builds on ADR 0004, ADR 0016 and ADR 0017. Tracked in AWAI-3088, JUN-1070 and AWAI-507.

## Context

62 archived `cloud-itonami` repositories each hold one municipality's record: `organization.edn` (official identity),
`data/datascript-tx.edn` (an ordinance catalog: title, enactment date, official URL, retrieval date) and `blueprint.edn`.
`catalogs/datasets/municipality.json` only referenced them. Owner direction (2026-11-17): the user's own single
assistant should be able to help with administrative procedures through skills, mcp and workflows, not one bot per
municipality; the registry may grow to several GB and hold data.

## Decision

1. `skills/knowledge/municipal-ordinance-knowledge`: `SKILL.md`, `references/index.json` (id, country, names, official URL,
   ordinance count) and `references/municipality/<id>/{blueprint,organization,datascript-tx}.edn` copied verbatim at the
   pinned commit and checked against the dataset catalog sha256. The skill says plainly that the data is an index of rules
   and where to read them, not their text or the procedures.
2. `workflows/municipal-procedure-guide`: a recipe (identify, lookup, read the primary source, checklist, hand off) that
   requires the skill, stops on a municipality outside the archive, a need for personal data, or a request to file on
   the user's behalf, and never executes automatically. Network fetches happen only after the user approves that exact
   request (the client-runtime consent rule).
3. Provenance as in ADR 0017: one source entry per repository, skill `sourceRefs`, inventory registrations (the workflow is
   registered on the first source). Builder: `scripts/build_municipality_knowledge.py`.

## Not decided here

- Archiving or deleting the 62 repositories (separate, with confirmation).
- Richer procedure data (steps, forms, fees); the archive holds none yet.
- Per-municipality agents: not created; one user assistant uses the skill and workflow.
