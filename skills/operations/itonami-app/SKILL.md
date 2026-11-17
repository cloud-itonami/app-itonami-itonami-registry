---
name: itonami-app
description: Search the Itonami actor catalog and open the Itonami app. Use when the user needs a worker for a task or wants to continue work in the app.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-cloud-itonami-app/tree/aa7ea0cb145a2c9b66e68b4fd029f3fd51bf88b8
    compatibility:
      hermes: '*'
      desktop: '*'
license: AGPL-3.0-or-later
---

# Itonami App

The bundled `itonami-fleet` MCP server (`bin/itonami-mcp`) serves the
actor catalog. It needs no session and makes no network calls.

## Search the catalog

Call `fleet_search` with any of `text`, `domain`, `isic`, `iso3166`,
`maturity`, `execution`, `callable`, `limit`. Every field is optional.
Results carry `repo`, `id`, `name`, `domain`, and execution info.

```
fleet_search {"text": "invoice triage", "callable": true, "limit": 5}
```

`fleet_call` is not on this host. When a hit names a repo the operator
can run, say which repo and entrypoint to use instead of calling it.

## Open the app

Call `itonami_open` with `{}`. It answers the app identity, the UI
resource, and the local URL (`http://127.0.0.1:1338` by default,
`CLOUD_ITONAMI_PORT` overrides). It never needs a session or arguments.
