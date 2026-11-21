---
name: egov-seido-packs
description: Read the Itonami institution packs (seido) that say which government procedures may apply to an address change, with their primary legal sources, deadlines and review state. Use with the Shakai, Kaisha and Matsuri e-government profiles, or when a user in a covered country asks what to file after moving.
license: AGPL-3.0-or-later
metadata:
  hermes:
    version: 0.1.0
    author: network-awai
    source: https://github.com/cloud-itonami/app-itonami-egov/tree/2db4b704e22fd84fea3e898acd5730725e2b67dd
    compatibility:
      hermes: '*'
      desktop: '*'
---

# E-government institution packs

`references/seido/*.edn` are verbatim copies of the institution packs in `cloud-itonami/app-itonami-egov` at `2db4b704`. Each pack holds, for
one country: procedures (who, when it applies, deadline, where to submit), the primary legal sources with retrieval
date and sha256, subdivisions (real municipalities are marked `:fixture false`; test ones `:fixture true`) and local
reference documents. `references/index.json` lists the packs, their review state and procedures.

The packs are evaluated by the pure functions in `src/itonami/egov/core.cljc` of the same repository (the Gyosei screen
in the Itonami app and the egov profiles use them). This skill carries the data so an assistant can read it.

## How to answer

1. Find the country in `references/index.json`. If there is no pack, say the procedures are not covered; do not answer
   from memory. A pack that needs a subdivision (for example the United States without a state) gives no candidates.
2. If today is after `review-by`, say the pack is out of date and stop; do not give candidates from it.
3. Give the procedures as candidates, each with its source title, issuer, retrieval date and URL. Say that the
   authority decides whether the filing is required or accepted. While `review-status` is `:unreviewed`, do not
   propose submitting anything.
4. Local references of a municipality are rules to read, not procedures. For municipalities without a pack entry, use
   `skill/municipal-ordinance-knowledge`.

## Limits

- No expert review yet. Only what each pack lists is covered.
- Do not collect personal data. Nothing here files, signs, pays or sends on the user's behalf.
