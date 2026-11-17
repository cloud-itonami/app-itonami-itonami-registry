---
name: itonami-measured-proposal-handoff
description: Prepare a deduplicated proposal from measured observations and verify a separate publisher handoff.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-arbitrage/tree/2233648e8757628f8ecfb97127ae498ceaa73692
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-measured-proposal-handoff

Read the selected owner ledger and actual observations within the requested interval. Record source time, snapshot identity and any simulated/devnet premise; an unbacked paper market is not a real collateral or settlement result.

Prepare a bounded proposal with stable identity, evidence references, kind and requested action. Check the owner proposal queue for duplicates. Save only to the caller-authorized draft/pending destination and read back the artifact.

A separate publisher may own delivery. Record drafted, queued, accepted and read-back states separately. If local storage or the publisher is unavailable, retain an honest blocked/pending status; do not invent a POST or assume the next scheduled tick delivered it.

Financial transactions, external contact and public posting are separate caller-authorized operations. This procedure may propose an action, but creates no spend capacity, schedule or external publication on its own.

Pinned derivation inputs are in itonami.json and catalogs/sources.json; owner runtimes and profiles are referenced, not imported.
