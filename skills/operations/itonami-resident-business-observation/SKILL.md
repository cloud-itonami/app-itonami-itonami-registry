---
name: itonami-resident-business-observation
description: Inspect resident business bot state, assignments and activity receipts while keeping lifecycle and spend changes owner-scoped.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-cloud-itonami-isic-8121/tree/7445d3ce7f01fa2cfe5198ada2e52aadfcdb251a
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-resident-business-observation

Resolve the actual resident runtime and its selected bot/business identity. A blueprint/catalog entry describes a business; it is not a running instance, verified identity or active wallet position.

Within caller-authorized read scope, compare the owner status, assignment/position and recent activity/event receipts. Preserve each route's response shape (bare list, events or data wrapper); a mismatched parser must not silently report zero activity.

Distinguish configured, launched, actively producing evidence, held/backoff and failed measurements. Read the classified correction state and budget before treating held as dead. Authentication errors are not transient inference errors, and a successful creation response alone does not prove a live tick.

Report observed state and the missing next receipt. Starting/resuming, relaunching or raising credit changes spend capacity and needs separate owner authorization. Credentials, signing keys, schedules and identity remain in the owner repository/application stores.

Pinned derivation inputs are in itonami.json and catalogs/sources.json; owner runtimes and profiles are referenced, not imported.
