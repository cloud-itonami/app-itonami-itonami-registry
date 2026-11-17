---
name: corporate-entity-knowledge
description: Look up what the Itonami archive knows about a company by its LEI or name, covering verified public-registry facts, the company profile and the text of its published Terms of Use. Use when a user asks about one of these companies or their terms.
license: AGPL-3.0-or-later
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-cloud-itonami-lei-06btx5uwzd0gq5n5y745/tree/2f9e5f343ee0cadd7c08a729cacc1d907e020915
    compatibility:
      hermes: '*'
      desktop: '*'
---

# Corporate entity knowledge

This skill carries the Itonami archive of 185 legal entities, keyed by LEI (ISO 17442). The facts come from public
registries and the companies' own sites; each entity folder is a verbatim copy of an independent archive and is **not
affiliated with the company**. It is reference material, not legal advice.

## How to answer a question about a company

1. Open `references/index.json`. Find the entity by `lei` (exact) or by `name` (case-insensitive substring; confirm with
   the user if several match). Each row has `jurisdiction`, `website`, `ticker` and the `dir` of its folder.
2. Read only what the question needs from `references/lei/<lei>/` (lower-case LEI):
   - `blueprint.edn`: short profile (legal name, address, phone, website, ticker, retrieval note). Start here.
   - `facts.edn`: verified registry facts (legal form, status, parent/ultimate-parent or the reporting exception),
     each with its source URL and retrieval time. Use it for ownership and status questions.
   - `citations.edn` and `CORRECTIONS.md` (only for some entities, listed in the index `files`): the catalog of what each
     fact was checked against, and the corrections applied to it. Read `CORRECTIONS.md` first when it exists.
   - `tos.journal.edn`: the full text of the company's published Terms of Use as tx-data. It is long; search it for the
     clause in question instead of reading it whole, and quote sparingly.
3. State where the answer comes from (file and the `:source/retrieved-at` or retrieval date). These files are snapshots
   from 2026; say so, and do not claim they are current. For anything that matters, tell the user to check the company's
   own current page.
4. If the entity is not in the index, say the archive does not cover it. Do not guess from memory.

## Limits

- Terms of Use text is the company's copyright; use it to answer and cite, not to republish.
- Nothing here grants authority to act for or contact the company.
