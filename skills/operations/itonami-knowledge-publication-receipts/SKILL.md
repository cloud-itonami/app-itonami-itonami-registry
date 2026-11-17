---
name: itonami-knowledge-publication-receipts
description: Check a knowledge ledger-to-index publication by separating source persistence, block readback and serving-root evidence.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-bpmn/tree/7de41855639c75b561ab80981fc3a6c0d49ff9b5
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-knowledge-publication-receipts

Resolve the actual ledger, catalog generator, block publisher and serving-root owner. Keep source claims and dataset metadata attributable, and use the owner's current reader/identifier contract. For multiple EDN entities, verify the complete serialized form with the owner reader rather than assuming every line was consumed.

Under caller-authorized scope, run the owner catalog/index build and retain its input revision, root CID and catalog digest. For publication, compare each required block's fetched bytes against its CID; an upload response or HTTP 200 alone does not establish byte identity.

Keep Git integration, storage-plane persistence, root-pointer update and the public serving-root receipt separate. Confirm which immutable root the actual serving process names, not merely the root the local build produced. Pending writes and unavailable gateways remain pending or unmeasured.

If another writer has already integrated the same revision, verify ancestry/readback before retrying. Preserve WIP and use an isolated checkout for repairs. Do not reset a resident checkout, rotate credentials or deploy as a side effect of inspecting the pipeline. Return the measured boundaries and unresolved stage.

Pinned derivation inputs are in itonami.json and catalogs/sources.json; owner runtimes and profiles are referenced, not imported.
