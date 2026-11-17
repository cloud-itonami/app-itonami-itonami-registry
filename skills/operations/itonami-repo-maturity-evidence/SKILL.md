---
name: itonami-repo-maturity-evidence
description: Assess repository maturity from the owner collector and its measured corpus; use when deciding one actionable repository improvement.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-bot-fleet/tree/b6120bb7214ac92b14e81c865c34048b14e5f762
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-repo-maturity-evidence

1. Bind an explicit repository scope, collector revision and output location. Read the owner collector's current invocation rather than using an old profile command.
2. Run only the authorized evidence collector, recording observation time, corpus size, exit status and artifact references. Missing or refused collection remains unmeasured.
3. Read the generated maturity evidence and trace one gap to its underlying contracts, tests or missing receipt. Preserve the difference between an observed failure and missing coverage.
4. Propose one scoped improvement and its verification criterion. A source count, passing catalog or generated score does not establish deployed or physical behavior.
5. Report the collector receipt, finding and unresolved qualification. Leave score generation, merges and owner policy changes to the owning workflow.

Source contracts are pinned in itonami.json and catalogs/sources.json. Runtime implementations and existing profiles remain in their owning repositories.
