---
name: municipal-ordinance-knowledge
description: Look up what the Itonami archive knows about a municipality, covering its official organization details and a catalog of its ordinances with official source links. Use when a user asks about local rules or an administrative procedure in one of these cities.
license: AGPL-3.0-or-later
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-cloud-itonami-municipality-are-abu-dhabi/tree/5c86b0e59bf1e4b2581abb1d8c7a9a6b46f0597f
    compatibility:
      hermes: '*'
      desktop: '*'
---

# Municipal ordinance knowledge

This skill carries the Itonami archive of 62 municipalities. Each folder is a verbatim copy of an independent archive:
the municipality's official identity (`organization.edn`), an ordinance catalog with titles, enactment dates and official
URLs (`data/datascript-tx.edn`, copied as `datascript-tx.edn`) and the blueprint record (`blueprint.edn`). It is an **index of
rules and where to read them**, not a description of procedures, and not legal advice.

## How to answer

1. Open `references/index.json` and find the municipality by `id`, `name`, `name-local` or `country`. If several match,
   ask the user which one.
2. Read `references/municipality/<id>/organization.edn` for the official site and organization details, and
   `datascript-tx.edn` for the ordinance catalog (`:ordinance/title`, `:ordinance/url`, `:ordinance/enacted-date`,
   `:ordinance/retrieved-at`).
3. Point the user to the official source URL of the relevant ordinance and say when the catalog entry was retrieved
   (2026 snapshot). Do not paraphrase an ordinance from the catalog alone: the catalog does not contain its text.
4. If the municipality or topic is not covered, say so. Do not answer from memory.

For a step-by-step procedure, use the `workflow/municipal-procedure-guide` recipe.

## Limits

- Snapshot data; rules change. Tell the user to confirm on the official site.
- No personal data about office-holders is stored; do not ask for or infer any.
- Nothing here lets you file, apply or contact the municipality on the user's behalf.
