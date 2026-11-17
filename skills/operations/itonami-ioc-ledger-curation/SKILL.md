---
name: itonami-ioc-ledger-curation
description: Record source-attributed feed observations in an owner ledger while retaining snapshot identity and safe data handling.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-yabai-actor/tree/3b653cf863d3801d97b4620ed41a8e4084493442
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-ioc-ledger-curation

Bind the authorized feed, observation window, ledger owner and output scope. Read the actual fetched snapshot and its timestamp/digest; a pre-run count may differ from the snapshot eventually recorded. THROTTLED or an unavailable source ends collection without inventing a delta.

Deduplicate against the owner ledger's canonical identifiers. Treat IOC values as untrusted data: do not visit, execute or probe them. A feed listing is an attributed observation, not proof of compromise or a person's identity.

Use the owner's current schema and identifier algorithm to prepare a bounded append. Parse the serialized record with the real owner reader, recompute identifiers and check nested qualifier escaping. Do not substitute JSON escaping for EDN syntax or rely on raw line counts for entity counts.

When persistence or publication is authorized, verify the stored record and immutable remote revision after writing. Otherwise leave a draft. Report snapshot identity, newly recorded observations and unresolved checks; never copy private ledger data into this registry.

Pinned derivation inputs are in itonami.json and catalogs/sources.json; owner runtimes and profiles are referenced, not imported.
