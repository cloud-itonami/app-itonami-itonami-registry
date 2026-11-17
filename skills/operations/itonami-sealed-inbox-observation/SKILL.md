---
name: itonami-sealed-inbox-observation
description: Observe sealed inbox metadata through an authorized mail-relay client; use for delivery and relay health checks.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-mail-relay/tree/9de19c3f320442a8851beffef5d8c543cd875434
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-sealed-inbox-observation

1. Bind the authorized inbox scope and observation window to the owner-configured metadata client. Keep account configuration and credentials in their existing application stores.
2. Confirm the current API response contract. Sealed payloads may omit plaintext subjects; do not infer body or subject content from opaque envelopes.
3. List or get only authorized metadata. Record opaque references, counts, timestamps and errors in the caller-selected private evidence location; publish only the permitted aggregate.
4. Distinguish authentication refusal, unreadable payload, no matching message and failed measurement. Do not infer successful delivery from client configuration alone.
5. Return the bounded observation and next verification needed. This procedure never decrypts, sends, deletes messages, closes accounts or rotates credentials.

Source contracts are pinned in itonami.json and catalogs/sources.json. Runtime implementations and existing profiles remain in their owning repositories.
