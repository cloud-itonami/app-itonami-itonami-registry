---
name: itonami-provider-capability-observation
description: Compare provider capability observations with actual serving state; use for model or multimodal availability reviews.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-bot-fleet/tree/b6120bb7214ac92b14e81c865c34048b14e5f762
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-provider-capability-observation

1. Bind the previous and current owner observation references, model identifiers, timestamp and intended modality. Do not copy private ledger contents into the registry.
2. Compare declared capability, accessible candidate, loaded model, serving endpoint and successful modality-specific request separately. A download count or model listing establishes none of the later stages.
3. If authorized, use the owner's bounded probe with an explicit target, process lifetime and resource budget. A probe that launches a temporary service has process and network effects; discovery alone does not authorize it.
4. Preserve refusals, quota errors, missing credentials and unavailable targets as separate observations. Do not replace missing results with presumed capability.
5. Report the observed delta and evidence boundary. Follow the caller's notification intent when nothing meaningful changed; changing routes or persistent configuration requires separate authorization.

Source contracts are pinned in itonami.json and catalogs/sources.json. Runtime implementations and existing profiles remain in their owning repositories.
