# ADR 0017 LEI archives as agent knowledge (corporate-entity-knowledge skill)

Status: proposed, 2026-11-17. Builds on ADR 0004 (dataset catalogs) and ADR 0016. Tracked in AWAI-3069, JUN-1070 and AWAI-507.

## Context

185 archived `cloud-itonami` repositories each hold the archive of one legal entity keyed by LEI: `blueprint.edn`
(legal name, address, website, ticker), `facts.edn` (verified public-registry facts) and
`80-data/public/tos.journal.edn` (text of the published Terms of Use). `catalogs/datasets/lei.json` only referenced them.
Owner decision (2026-11-17): the purpose is that an itonami agent knows about these organizations and can answer
questions about them, and the repositories are then archived or deleted.

They are knowledge, not a persona (a profile or bot per company would be 185 bots) and not a procedure
(185 skills).

## Decision

1. One skill, `skills/knowledge/corporate-entity-knowledge`, carries the knowledge: `SKILL.md` (how to look an
   entity up, cite and limit answers), `references/index.json` (lei, name, jurisdiction, website, ticker, folder) and
   `references/lei/<lei>/{blueprint,facts,tos.journal}.edn` copied verbatim at the commit pinned in the dataset
   catalog, each checked against its recorded sha256. An agent reads the index, then only the needed file
   (progressive disclosure).
2. Provenance: one `catalogs/sources.json` entry per repository (`lei-<lei>-<commit8>`), `sourceRefs` on the skill, and
   a registration on each repository's inventory row. `catalogs/datasets/lei.json` stays as the reference catalog.
3. The builder is `scripts/build_lei_knowledge_skill.py`; it executes nothing from the source.

## Not decided here

- Archiving or deleting the 185 repositories (a separate step, after the substance is confirmed and with its own
  confirmation); 53 of them have non-default branches that need a check first.
- Refreshing the snapshots (the files are 2026 snapshots; the skill says so).
- Terms-of-Use text is the companies' copyright; the skill limits use to answering and citing.

## Consequences

- An agent installed from the registry can answer from these 185 entities without cloning 185 repositories.
- About 12 MB is added to the registry.
