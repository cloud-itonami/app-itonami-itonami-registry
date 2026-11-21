# Itonami Registry

Reusable bot role templates, operational skills, MCP connection definitions and workflow recipes for Itonami agents. Actual bot profiles remain owned by their existing GitHub repositories. Registry publication grants no execution authority, changes no running profile and activates no scheduler.

## What is in it

The Itonami Registry is the Hermes registry's equivalent for Itonami (ADR 0002). Same entry shapes, plus Itonami profiles, with the Hermes registry federated in.

| Type | Folder | What it is |
|---|---|---|
| **Itonami profile** | `profiles/` | A Hermes-layout profile (SOUL.md, profile.yaml, config.yaml, skills/) owned by another repository, pinned to a commit with per-file sha256. Install it as an Itonami Bot or a Hermes profile |
| Agent | `agents/` | Bot role templates |
| Skill | `skills/<category>/` | `SKILL.md` (agentskills.io frontmatter) |
| MCP | `mcp/` | MCP connection definitions |
| Workflow | `workflows/` | Itonami recipes |
| Model | `models/` | Provider model catalogs (murakumo) |
| **API** | `apis/` | A vendor-compatible API shape (entities, routes, the vendor resources and enums the source cites) declared by a repository's `manifest.json`, pinned to one commit with per-file sha256. Shape only: no execution, not runtime-qualified, grants nothing (ADR 0005) |

**Terms are Hermes's own.**
- A profile is the persistent home; an Itonami profile is a Hermes profile.
- A Bot is a profile presented in a roster with one canonical Bot Chat. Every Bot is a profile; not every profile is a Bot.
- Messaging bots and subagents are different things.

**Site and API.**
- `scripts/build_site.py` builds a static site and JSON API (`api/v1/index.json`, `categories.json`, `models.json`, `registries.json`, `entries/<registry>/<type>/<id>.json`), published by GitHub Pages.
- The Hermes registry (fathah/hermes-registry) is federated as `hermes-registry/<type>/<id>`: metadata only, pinned commit, upstream checksums.
- The [association rules viewer](https://cloud-itonami.github.io/app-itonami-itonami-registry/assoc/) filters by country or region and ISIC. It shows catalogued titles, citation links, retrieval dates and reference sections when recorded. The site build verifies the bundled [association snapshots](datasets/assoc/) against `catalogs/datasets/assoc.json` and projects the rules into inert HTML data. The original association repositories are historical provenance. The build reads these snapshots locally, and the viewer links to the verified EDN included in the same static artifact. The built `assoc/` directory uses relative assets and searches its bundled snapshot locally, so it can be included in a future Tauri frontend alongside the Registry index. External citations are opened on demand and need connectivity.
- The [Android wrapper](android/assoc/) packages the same viewer for offline lookup on Awai OS.

**Contributing.** See [CONTRIBUTING.md](CONTRIBUTING.md); profiles are registered with `scripts/add_profile.py`.

## Initial entries (retained)

| Type | ID | Purpose |
|---|---|---|
| agent | fleet-health-auditor | Measured bot and cron fleet review |
| agent | physical-ai-evidence-bot | Domain simulation evidence and bounded improvement |
| skill | itonami-cron-health-audit | Correlate cron records, scheduler logs and final output |
| workflow | fleet-health-review | Collect, classify and report fleet evidence |
| workflow | evidence-measured-improvement | Bind a domain premise, measure and propose one improvement |
| mcp | murakumo-web | Connection definition for the owner-installed web-plane server |

The physical-AI agent includes ISIC 7020 and ISCO 2421 parameter examples. Templates are partial scaffolds; they have no profile identity, credentials, enabled tools or cron jobs. Each target repository binds its parameters and policy before use. The ISCO example preserves the source's hypothetical physical premise.

## Discover and consume

Start at [llms.txt](llms.txt), then [llms-full.txt](llms-full.txt). The public discovery endpoint is https://raw.githubusercontent.com/cloud-itonami/app-itonami-itonami-registry/main/index.json. Resolve the registry to one immutable commit and verify the complete selected folder checksum before use.

Skills use SKILL.md frontmatter; MCPs, agents and workflows use Hermes manifest shapes. itonami.json contains supplemental inputs, effects and authority requirements. Wildcard Hermes/desktop version fields express no declared version filter; only catalog format has been checked. Runtime installation compatibility has not been qualified. workflow.json uses an Itonami recipe schema and requires a compatible reader; it is not a proven Hermes executable workflow.

[catalogs/tools.json](catalogs/tools.json) indexes eight Murakumo MCP tools, four portable user-test MCP tools, one native fleet catalog tool, two mihari, five dandori, eleven kaikei and eight kumitate itonami dapp tools, three plugin-hermes tools and three ZAP plugin tools, with provider identity and input contracts. [catalogs/sources.json](catalogs/sources.json) records pinned derivation inputs and file hashes. Tool discovery is not a successful live invocation.

## API registry

The registry's own API registry ([ADR 0005](docs/adr/0005-api-entries.md)) holds **1,028 `api` entries**. They come from the clean-room compat actors and API clients in kotoba-lang, such as [com-circleci](https://github.com/kotoba-lang/com-circleci): 856 compat L4, 171 compat L5 and 1 client L3. Each entry is `apis/<repository>/manifest.json`, and its qualified identity is `itonami-registry/api/<repository>`.

What an entry records:
- the declared entities and routes;
- for L5, the vendor OpenAPI source with its resources and enums, as claimed by the source;
- the actor's DID and Wasm CID, as asserted by the source;
- the pinned commit, with sha256 for each of the owner's files.

What it does not claim: the shape is not runtime-qualified, nothing is executed, the CID is not verified, and no authority is granted. A reverse domain (for example `com.stripe`) is shown only when the public origin-domain extract ([catalogs/origin-domains.json](catalogs/origin-domains.json), ADR 0005 amendment 1) records it: 102 entries are `recorded` and 926 remain `unverified`.

[catalogs/api-classification.json](catalogs/api-classification.json) classifies all 1,090 repositories in the AWAI-59 target set (`com-*`, dotted names, `cloud-*`):
- 1,028 are `api` entries.
- 62 are `unclassified`, each with a reason: 44 have no API manifest, 9 are dataset snapshots, 5 are connector contracts and 4 are private (counted only).

No repository had a skill, profile or bot marker. [catalogs/api-relations.json](catalogs/api-relations.json) links API entries to the itonami dapps (MCP, skill or profile entries) that implement or consume the same shape. The repositories stay in kotoba-lang, and nothing was moved or renamed.

Regenerate with `python scripts/build_api_catalog.py --clones <dir of kotoba-lang clones> [--refresh] [--check]`.

## Itonami dapps for agents

| Type | ID | Purpose |
|---|---|---|
| mcp | mihari | Sentry-compatible error grouping and triage rules ([app-itonami-mihari](https://github.com/cloud-itonami/app-itonami-mihari)) |
| mcp | dandori | Linear-compatible export conversion, cycle progress, estimate and SLA checks ([app-itonami-dandori](https://github.com/cloud-itonami/app-itonami-dandori)) |
| skill | itonami-sentry-error-triage | Triage Sentry data an operator already holds with the mihari tools |
| skill | itonami-linear-issue-planning | Check Linear exports an operator already holds with the dandori tools |
| mcp | kaikei | MoneyForward / freee / Yayoi / QuickBooks Online / Xero-compatible journal import, checks, trial balance, P&L and balance sheet, invoices (per-rate consumption tax, qualified-invoice contents, posting; Xero, QuickBooks Online, freee請求書, MoneyForward クラウド請求書, Zoho Invoice and FreshBooks shapes), bank, card and expense statements (OFX, 全銀 data, statement CSV, Ramp, Brex, Expensify and BILL; reconciliation, invoice settlement, approved posting) and format conversion ([kaikei](https://github.com/cloud-itonami/app-itonami-kaikei)) |
| skill | itonami-ledger-statements | Build statements from journal exports an operator already holds with the kaikei tools |
| skill | itonami-invoices | Draft, import, check and post invoices with the kaikei tools, without the NTA or any invoicing service |
| skill | itonami-statement-reconciliation | Reconcile downloaded bank, card and expense statements and post only approved lines with the kaikei tools, without any bank or expense service |
| mcp | kumitate | CircleCI-compatible config checks, processed pipeline (matrix, filters, requires DAG), config-process YAML, API v2 shapes, run-record and JUnit summaries ([app-itonami-kumitate](https://github.com/cloud-itonami/app-itonami-kumitate)) |
| skill | itonami-circleci-pipeline-planning | Check a config.yml an operator holds and explain which jobs a branch or tag runs, with the kumitate tools |

mihari, dandori and kaikei are stdio MCP servers whose tools are pure functions over the passed text. They contact no vendor (sentry.io, linear.app, MoneyForward, freee, Yayoi, QuickBooks Online, Xero, Zoho, FreshBooks, Ramp, Brex, Expensify or BILL), bank, card issuer or the NTA, make no payment, and store nothing. mihari and dandori are recorded in catalogs/targeted-public-sources.json because those repositories postdate the 2026-10-10 inventory. kaikei's registrations sit on its existing inventory row, with their own source commit. Registration adds none of them to a profile.

kumitate is a native Kotoba program built only with the Amu selfhost compiler. Its owner starts it as a Streamable HTTP MCP server on a loopback address (the native runtime has no stdin yet). Its tools are pure functions over the config, run records or JUnit reports the caller passes. It fetches no orb or CircleCI function, contacts no CircleCI or VCS service, runs no job and stores nothing. catalogs/api-relations.json links the com-circleci API entry to mcp/kumitate (ADR 0005). Registration adds it to no profile.

## Compat actors

`compat/<slug>/` holds the clean-room, API-compatible actors that used to be one kotoba-lang repository each (`com-circleci` and 1,026 others; ADR 0006). `compat/index.json` lists them with origin commit and folder checksum; `catalogs/compat-sources.json` pins the origin. They are not Hermes entries, grant no authority, and publication claims no runtime or vendor-API qualification.

## Ownership and federation

[kotoba-registry](https://github.com/kotoba-lang/kotoba/tree/b94158fd48ec541b70d3c455912a06f407537ddc/lib/kotoba.kotobaRegistry) (now `lib/kotoba.kotobaRegistry` in kotoba-lang/kotoba) remains the Kotoba extension catalog. Its github-forest MCP and github-forest-maintenance skill are referenced in catalogs/external-registries.json, not copied. Registry-qualified identities prevent collisions. Federation requires a consumer that understands the external registry descriptor.

Source code, per-bot SOUL/config/cron definitions and domain policies stay in the owning repositories. Sessions, credentials, runtime state and ledgers stay in their application homes. This registry is separate from west pins and from signed CID-pinned language package admission.

## Maintain

Use Python 3.11 or later in an isolated environment and install requirements.txt, then:

```text
python scripts/validate.py
python scripts/build_index.py
python scripts/build_index.py --check
python -m unittest discover -s tests
python scripts/build_api_catalog.py --clones /path/to/kotoba-lang --check   # needs local clones
```

For release verification with authenticated GitHub CLI, run `python scripts/verify_sources.py`. To reproduce the bounded MCP discovery probe, run `python scripts/probe_mcp.py --checkout /absolute/path/to/kotoba-lang/murakumo`; it reads the pinned script with Git and sends no valid tool invocation. The existing checkout is not modified.

index.json is generated. CI validates schemas, checks catalog freshness, source references, entry integrity and dependencies, and rejects duplicated external entries. Change the version when an entry changes. Keep immutable source references and describe the actual validation boundary.

See [ADR 0001](docs/adr/0001-registry-ownership.md) and [validation receipt](docs/validation.json). New authored registry content and tooling are MIT; the source repositories retain their own licenses. Upstream profiles and runtime implementations have not been copied. Vendored Hermes schemas retain their MIT attribution in NOTICE.

## Organization inventory and expansion

The 2026-10-10 inventory covers 4,710 GitHub repositories across both organizations. The public [machine-readable inventory](catalogs/inventory.json) contains 4,614 repositories: every nonempty public default branch has a complete recursive filename survey; one repository has an empty default branch. Private repositories are counted only (96); their names and contents are omitted. Filename markers are candidates, not semantic or runtime qualification. See [coverage and selection decisions](docs/inventory-2026-10-10.md).

The catalog now has **47 entries**: 26 skills, 13 agent templates, 6 MCP connections and 2 inert workflows, plus **37 provider-qualified tool references**. Added roles cover repository maturity, provider capabilities, research corpora, sealed inbox observation, learning material drafts and independent evidence review. Added skills also cover portable user tests, content-addressed receipts, host connector contracts, definition inspection, guest admission and system-dynamics evidence. These are Itonami operational adaptations; upstream implementation and generic language skills retain their owners.

The user-test connection is source-inspected and has a checked fail-closed launcher; its target runtime is not qualified. The Murakumo discovery probe sends zero valid tool calls and performs no live network operation. The inventory includes candidate and deferred decisions; neither these records nor publication enables a profile or tool.

## Remaining candidate review

The [2026-10-11 review](docs/candidate-review-2026-10-11.md) resolves all 37 previously pending/deferred candidate owners into explicit source-scoped decisions: registered, deduplicated, source-only, deferred or already-owned. Nine additional operational skills, five role scaffolds, the current guest-Wasm fleet catalog MCP and four native tool references were added. [catalogs/candidate-reviews.json](catalogs/candidate-reviews.json) preserves reviewed commits, evidence hashes and reasons. Existing profiles remain in their owner repos; initial registry entries and external kotoba-registry ownership are retained.

The fleet catalog connection is source-inspected and publishes fleet_search only. Its owner-built guest and startup are untested. ZAP plugin descriptors are discovered by literal AST, with no scans or configured targets. Catalog publication neither installs an adapter nor enables effects.
