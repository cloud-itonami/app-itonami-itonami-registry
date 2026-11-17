---
name: itonami-data-source-reconciliation
description: Reconcile a research corpus catalog with source, license and bounded HTTP evidence; use before consuming a public dataset.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-loop-data-source/tree/7468f6517514146ad10cb38e8cdc5131282b60b7
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-data-source-reconciliation

1. Read the owning catalog and choose the smallest source scope needed for the research question. Record source identifier, retrieval boundary and catalog revision.
2. Inspect the current source license and access terms for the intended use. A catalog label is a claim to verify, not perpetual legal permission.
3. Run the authorized owner verifier once. Record response status, content/body checks and timestamp. HTTP 200 alone may be a login page or unrelated body; a missing or refused measurement stays unmeasured.
4. Keep public corpus references separate from host-local snapshots and participant or lead records. Verify actual join keys and report null or unmatched keys rather than inventing associations.
5. Return a source receipt with provenance, usage assumptions and unresolved checks. Acquiring credentials, subscriptions, contacting people or writing another owner's corpus is separate work.

Source contracts are pinned in itonami.json and catalogs/sources.json. Runtime implementations and existing profiles remain in their owning repositories.
