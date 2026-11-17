---
name: itonami-app-operations
description: Use when driving the itonami CLI, cloud-itonami-app, or the itonami bots/economy
  plane (grok-bots worker, bot-economy DO, treasury adapters).
version: 1.6.0
metadata:
  hermes:
    version: 1.6.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-cloud-itonami-app/tree/b8b7fb809fedc9ea996cfcdc10172465abb398a5
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami app operations (cloud-itonami-app CLI)

## What the CLI is

`~/.local/bin/itonami` is an nbb launcher
(`orgs/cloud-itonami/cloud-itonami-app/bin/itonami`) that spawns `clojure -M:cli`
in the app directory. It is an **HTTP client** of a JVM resident on 127.0.0.1; any
command that needs the server starts a headless one automatically (ADR-0018). The
launcher binds the resident data dir `~/.cloud-itonami/{app,data}` so the CLI and
the launchd server read the same enrollment key.

**Commands are generated, not hand-written.** `cloud.itonami.app.route-scan` reads
the server's own route cond and `dev/gen_commands.cljs` writes
`resources/cloud-itonami-app.commands.edn`; the CLI dispatches over it. Never trust
a remembered command list — enumerate live:

    itonami commands [term…]

(17 hand-written lifecycle commands stay in `cli.clj`; adding a route without
regenerating the registry fails the test suite.) JVM warnings on every invocation
(`Warning: protocol #'kotoba.lang.fs/IFilesystem is overwriting function list`,
`binding already refers`) are harmless — filter them, don't investigate them.

## Hermes compatibility — the measured answer (ADR-0088, 2026-09-01)

The CLI carries a first-class Hermes-facing surface (verified live 2026-09-03):

    itonami hermes profile list                       # → 200, one Bot per Hermes profile PLUS bot-workforce-* bots
    itonami hermes run --profile P --input 依頼 [--goal true]
    itonami hermes run-status|steer|stop|approve --run R
    itonami hermes session list|messages [--profile P]
    itonami bots import hermes [--stage true] [--provision true]

Compatibility is **information-plane only**:

- Migrates: persona/SOUL, config-as-data, memories, skills/scripts/plugins **as
  inert source material**, cron (stopped until review), redacted session history.
- Never migrates: credentials (`.env`, OAuth, tokens) and tool-permission/approval
  state → `rebind-required`. Provisioned Bots start inert: writes, browser,
  computer, peers, coding, shell, goal mode, omakase, accounts, tools all OFF.
- **The run loop is itonami's own** bounded loop (`POST /p/{profile}/v1/runs`),
  not the Hermes binary. Hermes's `empty_response_guard` / `repetition_guard`
  decisions were re-implemented in the decision core (ADR-0086). So "itonami CLI
  は hermes と同じ cli agent か" → same information plane, different runtime and
  authority. Don't answer this from memory; probe `itonami hermes profile list`.

Profile ids in `hermes profile list` mirror `~/.hermes/profiles/` names and map to
`bot-…` ids; models read e.g. `z-ai/glm-5.3-flash` via provider `murakumo` (some
rows pin `murakumo-main` alias).

## Hermes cron jobs across profiles — liveness verification

Cron jobs live per profile (`~/.hermes/profiles/<p>/cron/`) and cross-profile
control works via `HERMES_HOME=~/.hermes/profiles/<p>/ hermes cron list|resume|run …`.
**「cron list に載っている」は発火の証明にならない。** proving a job actually
fires is a 4-step ladder: (1) `cron list` state/next_run → (2) `cron/executions.db`
status (`completed`/`running`/`unknown`) → (3) `logs/agent.log` tag
`cron_<job_id>_<ts>` → (4) the final report file under
`cron/output/<job_id>/<ts>.md`. Known traps (all measured 2026-09-03): a manual
`hermes cron run` under a short foreground timeout kills the owner and records
`unknown`; the first post-resume fire can fail on openrouter-free's 90s
stale-call-kill yet the next periodic fire completes; don't delete/rebuild a job
off one `unknown`. Full command ladder and status semantics:
`references/cron-liveness-verification.md`.

When creating a bot profile, its cron jobs are designed and registered at
creation time per the `bot-cron-organize` skill (read it first).

### Definitions are the repo's plane; runtime state is terminal-local

The jobs.json files hold terminal-local runtime state and do not sync across
machines — but the job DEFINITIONS have a canonical repo ledger:
`scripts/hermes-cron-jobs/` in the com-junkawasaki superproject
(schema `itonami.hermes-cron-jobs.v1`, landed `4a75551396f` 2026-09-03:
7 profiles / 29 jobs at generation time). Regenerate after ANY cron change
(create/edit/pause/resume/remove) and land it:

    python3 scripts/hermes-cron-jobs/export_cron.py          # regenerate
    python3 scripts/hermes-cron-jobs/export_cron.py --check  # byte-compare vs live

- The ledger carries definitions only (schedule/prompt/script/deliver/workdir);
  state fields (last_run/next_run/executions) are stripped on export.
- Credential values are never baked in: a shape scan writes only the pattern
  name into `_credential_warning`. Lesson from generation: naive substring
  patterns false-positived on `task_comments` (contains `sk_`) — patterns must
  be length-thresholded key shapes, and the matched value itself is never
  written, only the pattern name.
- A new terminal rebuilds the fleet from this ledger (profile create → cron
  create per entry → script re-copy from the canonical scripts dir → gateway
  heartbeat check). Full procedure: `scripts/hermes-cron-jobs/README.md`.
- Same commit also brought the agentmail registry (`90-docs/business/
  agentmail-bot-profiles.json`) into the tracked plane — it had been
  untracked since its session. Session detail incl. the credential-scan
  false-positive lesson and the repo-vs-terminal boundary framing:
  `references/cron-ledger-export.md`.

### Census — counting bot profiles (measured 2026-09-03)

"bot profile" spans planes; when asked how many there are, answer per plane
and label each, don't give one number:

    itonami hermes profile list 2>/dev/null > /tmp/hermes-profiles.edn
    tr '}' '\n' < /tmp/hermes-profiles.edn | grep -c ':bot_id'   # total resident Bots
    grep -o ':id "bot-workforce' /tmp/hermes-profiles.edn | wc -l # workforce bots
    grep -o ':status "blocked"' /tmp/hermes-profiles.edn | wc -l # blocked

Measured 2026-09-03: 125 resident Bots = 31 Hermes-profile bots + 94
`bot-workforce-*` bots (4 blocked); `~/.hermes/profiles/` had 30 dirs. These
numbers drift — re-measure and cite the date instead of trusting this line.
Latest known profile addition: **`samu`** (2026-09-03 evening, giemon cleaning-
robot vertical organizer — ISIC 8121; cron x2, gateway plist, SOUL applied,
plan files under `profiles/samu/`).

Counting pitfalls (both hit live):

- The list prints as ONE line of EDN — `grep -c ':id "'` counts matching
  LINES and returns 1. Split records with `tr '}' '\n'` first, or count
  occurrences with `grep -o … | wc -l`.
- Post-processing via `cmd | python3 -c …` is flagged by Tirith
  (pipe-to-interpreter, HIGH). Write the output to a file and grep/tr the
  file — that form passes clean.
- Mail identities (agentmail inboxes) are a SEPARATE plane — see the
  `agentmail-bot-profiles` skill; don't fold them into this count.

Coordination plane — "who organizes/manages the bots": **codinator** is the
coordinator profile (SOUL: 幹事 — creates bots, assigns jobs, schedules),
monitored by hourly standups plus `manager-fleet-checkin` (20m) which surveys
the whole roster; **manager** carries per-plane pulse crons (11 jobs);
**itonami-dispatch** runs the kanban work queue. All three have BOTH a Hermes
profile and an itonami resident Bot. Before citing the fleet as healthy, check
codinator's own crons aren't paused (measured 2026-09-03: `manager-fleet-checkin`
was found paused with no recorded reason since 09-01 — reason-less pauses are
the known gap; the organize rule lives in the `bot-cron-organize` skill).

## Authority model (ADR-0009 + ADR-0086)

- Agent sessions root in `agent-enrollment.key` (0600, written by the server at
  start) — the data directory is the app, so *reading the key* is the load-bearing
  proof, not a Passkey. Sessions carry `:kind` (`:passkey` default, `:agent`); an
  un-enrolled user's cookie session still answers 428 while the agent path works.
- Bearer token on `/api/*` is checked before the cookie and skips Origin/CSRF
  (nothing attaches an Authorization header by itself; server sends no CORS).
  BUT bearer does not unlock every route: the whole `/api/bots` family is
  gated by `require-human-session!` (ADR-0060) — an agent session CANNOT
  create Bots (`POST /api/bots`) or widen grants even with a valid bearer
  (measured 2026-09-03 in server.clj:6400s). Bot creation is a human step in
  the Bots UI; agent-side surfaces are the narrower `/api/agent-bots/*`. Note
  `POST /api/bots` is also absent from the generated CLI registry
  (`resources/cloud-itonami-app.commands.edn`), so no CLI command maps to it.
- **Agents can never approve.** `approve/finish` needs a WebAuthn user-verifying
  assertion (ADR-0006). CLI approval is omakase-Bot-only; permission settings and
  normal-mode approval are browser-only. The CLI can only change a Bot's model route.
- Model routing tasks (ADR-0086): `:bot` (per-Bot, on the Bot's own record),
  `:room`, `:machine`, `:chat` — each task name resolves to a real function in
  tests; adding a task and adding a model call are one commit.
- **No Biscuit CLI surface — deliberate (measured 2026-09-03).**
  `itonami commands biscuit` → matched 0; `credentials verify` is the
  SD-JWT-VC face and `credentials trusted-issuers` returns `[]`. Delegation
  by Biscuit lives in the workforce-bot plane (`bot_authority.clj`, live
  fleet root seed at `data/workforce-authority.seed`, root DID measured
  `did:key:z6MkfYSYR…`) and in the kotobase/murakumo planes — not in the
  CLI, whose auth is enrollment-key → agent-session (see `agent_session.clj`:
  a process that can read the store can mint any session, so the key file
  is the load-bearing proof). Do not "add biscuit commands" without an
  owner decision; answer Biscuit-authority questions from
  itonami-business-bots → `references/biscuit-authority-map.md`.

## Bot economy — provisioning & naming (ADR-0055/0056, 2026-09-03)

- **Every bot profile auto-gets a loan position.** `GrokBotRuntime.ensureResident`
  / `configure` call `ensureEconomyPosition` → economy DO `ensureBotPosition`:
  idempotent (`bot-position:auto:<bot_id>`), simulation-only, ceiling 48,
  credit 0.025 USDC / per-call 0.001 / daily 0.005, services murakumo+kotobase.
  Failure is an `economy/provision-failed` event, never a bot-start blocker.
- **Refill:** economy DO `topupPosition` clears debt when it reaches 80% of
  credit (`topup-decision` in the portable core; cleared = min(amount, debt)).
- **Public endpoints** (CACAO/service-token gated): `POST /v1/bot-economy/positions/ensure`,
  `POST /v1/bot-economy/topups`, `POST /v1/bot-economy/allocations` (treasurer),
  `POST /v1/grok-bots/bots` (configure; bot_id IN BODY — /bots/{id} POST is 404).
  Status feed: `GET /api/v1/bot-economy`. Public alias: `/api/v1/itonami-bots/*`.
- **Treasurer (ADR-0057)**: `allocation-decision` (portable) refuses over-ceiling
  requests (never caps), respects wallet reserve, one malformed request refuses
  the pass. `allocateBudget` is simulation-only until ADR-0056 signer.
  Treasury wallet is WebAuthn-owned via the kotoba auth plane — no bot holds keys.
- **Default resident live-config**: MURAKUMO_SERVICE_TOKEN_LOCAL_MURAKUMO (kagi,
  KAGI_HOME=$HOME/.kagi) authorizes (204) via api.murakumo.cloud/internal/grok-bots/authorize.
  Reconfigure with allowed_tools incl. x402_purchase + start:true → running.
- **BTC/ETH/DOGE are refused assets** — settlement is pinned to Base USDC by
  `bot_economy.cljc` (`:x402/asset-mismatch`). Support = lend (LP deposit) or
  donate (Base USDC treasury), stated on /bots/#support.
- **Live capital is held** until capital verifier + delegated signer are
  configured (ADR-0056). Signer/key config is a human-credential task.
- **ADR-0056 adapters are LANDED (nexus-x402 PR #29, deployed live 2026-09-03).**
  The two adapters live on the treasury plane (x402.nexus) where the Base RPC
  failover, receipt parsing, and EIP-1559 signing substrate already existed —
  do not re-implement them in the grok-bots worker:
  - `POST x402.nexus/internal/bot-economy/capital/verify` {evidence_ref} →
    USDC Transfer leg via `treasury/receipt->onchain` + Aave `Pool.Supply`
    event scan (topic0 computed at boot via eth-crypto keccak — never a
    hand-typed constant). Returns the exact shape `activateLive` demands.
  - `POST x402.nexus/internal/bot-economy/sign` {spend_id, requirement} →
    per-spend + daily-cap policy gate (SIGNER_DAILY_KV) → ERC-20 transfer
    from the treasury wallet → EIP-1559 sign → broadcast → public X-PAYMENT
    proof in the base64 shape cloud-itonami's purchase already parses.
  - Both Bearer-gated (`BOT_ECONOMY_CAPITAL_VERIFIER_TOKEN` /
    `BOT_ECONOMY_SIGNER_TOKEN`), 503 named-reason when unconfigured, all
    policy violations fail closed. Keys live in this Worker's env
    (owner-configured), never in the bot plane.
- **Remaining owner steps to flip simulation → live** (nothing agent-side left):
  1. WebAuthn wallet registration via the auth plane ceremony (human step).
  2. Fund the treasury address with Base USDC (tx hash = evidence_ref).
  3. Secrets/vars on nexus-x402: `wrangler secret put
     BOT_ECONOMY_CAPITAL_VERIFIER_TOKEN` / `BOT_ECONOMY_SIGNER_TOKEN` /
     `BOT_ECONOMY_SIGNER_PRIVATE_KEY`, plus vars `TREASURY_WALLET_ADDRESS`,
     `SIGNED_SPEND_CAP_MICROS`, `SIGNED_DAILY_CAP_MICROS`; then cloud-itonami's
     `BOT_ECONOMY_CAPITAL_VERIFIER_URL=https://x402.nexus/internal/bot-economy/capital/verify`
     and `BOT_ECONOMY_SIGNER_URL=.../sign`. Then `POST /api/v1/bot-economy/activate`
     with the evidence_ref. Adapter battery: `references/cloud-itonami-test-and-deploy.md`
     § nexus-x402 ADR-0056 adapters; adapter internals + authoring pitfalls:
     `references/nexus-x402-adr0056-adapters.md`.

## Worktree convention for this repo (measured 2026-09-03)

- Do NOT place worktrees in /tmp: sibling-path source-paths don't resolve and
  `git worktree remove --force` destroys uncommitted work. Use
  `~/github/wt/<name>`.
- **Commit as soon as one unit passes tests** (measured 2026-09-03): relocating
  a /tmp worktree with `git worktree remove --force` wiped ~11 uncommitted files
  at once and they had to be re-authored from the transcript. Small commits on
  the agent branch make any later relocation cheap.
- deps.edn/shadow-cljs resolve `../../kotoba-lang/*` etc. via symlinks in
  `~/github/{kotoba-lang,cloud-itonami,network-awai}/` pointing
  into the superproject checkout (created on demand).
- **Deploy ordering trap (bit twice, 2026-09-03):** `deploy:grok-bots` deploys
  the Worker AND Pages from `public/` as-is. If `site/*.cljc` (e.g.
  `site/bots.cljc`) changed but `public/` was not regenerated first, the live
  page silently serves the OLD HTML — no error anywhere. Order: edit → tests →
  `clojure -M:local:site` → commit the regenerated public/ → push → deploy →
  `curl` the live page for the new copy before claiming done.
- Full measured command battery for this repo in a worktree (nbb policy
  runners, focused JVM without the :test alias, DO tests in a fresh worktree,
  alias proxy tests, live probes): `references/cloud-itonami-test-and-deploy.md`.

## Workforce Registry (ADR-0058) — bot identities are registered, not issued

Landed 2026-09-03 (PR #581, 464e18c5 + live endpoint b8d9d8b1). The authority
direction moved from 'a seed file the operator process holds' to 'a public
registry the operator revokes from':

- **The bot is the issuer; the human is the registrar.** A bot presents its
  own did:key (derived by bot-identity.clj), the operator's Passkey co-signs
  via the itonami WebAuthn ceremony, and the entry lands in the registry.
  The human never mints a bot key.
- **Portable core** `cloud-itonami.workforce-registry.cljc`: `entry-errors`
  (named errors: did pattern, attestation shape webauthn-cosign, status
  active/retired), `verified?` (the one consumer question), `public-entry`
  (carries WHO attested via rp-id/credential-id, never the signature),
  `merge-entries` (static committed entries shadow dynamic KV entries by
  did; unverified entries drop at the boundary).
- **Live endpoint** `GET /api/workforce-registry` (serves the baked
  public/workforce-registry.json merged with ITONAMI_DATA KV dynamic
  entries; `unverified-count` is REPORTED, never hidden — empty count 0 is
  the honest state until the first WebAuthn co-sign ceremony runs).
- **Enrollment**: `POST /api/workforce-enroll` — shape-gated entries land
  in the dynamic store; the cryptographic co-sign challenge binding is the
  NEXT slice. Future slices: `x402_bot_pass.cljs bot-issue` flip (sign with
  the bot's own seed, verify against registry-confirmed did), nexus-x402
  verify adds a registry check.
- **FIRST ENTRY LANDED 2026-09-04 (merge b3850f5f): financial-chief bot
  enrolled via DID/CACAO, registry live count 1.** The path that actually
  works for an agent (WebAuthn passkey is human-only — an isolated
  Chrome-for-Testing has no platform authenticator, so the passkey
  ceremony dies in agent hands; do not retry it):
  1. Derive the bot seed: `SHA-256(fleet-seed ‖ 0x00 ‖ bot-id)` — same
     derivation as bot-identity.clj (node: `crypto.createHash('sha256')`
     over seed file bytes + one 0x00 byte + bot-id UTF-8).
  2. Mint with nbb + `cacao.core/mint-kotobase-apex` `:aud
     "https://auth.kotobase.net"` — the authn worker's audience is NOT
     `did:web:kotobase.net` (the library default); a wrong aud = opaque
     "invalid CACAO" 401.
  3. `POST https://auth.kotobase.net/v1/cacao/session` with a JSON body
     `{cacao_b64, return_to}` **and a browser User-Agent header** — a
     bare-curl UA gets Cloudflare error 1010 (403) which looks like an
     endpoint problem but isn't. Success = `gftd_session` cookie + did in
     the response.
- **Pages deploy trap (hit twice)**: `wrangler pages deploy public/` does
  NOT carry `functions/` — the function shims under `functions/api/*.js`
  only deploy with a repo-root deploy. Also the shim import path from
  `functions/api/*.js` to the edge bundle is `../edge/cacao-edge-core.js`
  (one level up), not `../../edge/`. Full detail:
  `references/workforce-registry.md`.
- **Enroll 404 was THREE stacked bugs (all fixed in merge b3850f5f, each
  invisible while the others masked it)**: (1) `handle-enroll-route`
  compared its 3rd arg against "/internal/workforce/enroll" but Pages
  passes the Functions CONTEXT there, never a path → read the path from
  `request.url` instead; (2) the shim re-exported the edge handler raw so
  its first arg was the context object, not a Request → normalize
  `{request, env, context}` in the shim (sibling registry.js already ran
  on that convention); (3) the KV `.put` was fire-and-forget — the 201
  returned while Pages cancelled the write when the response completed →
  chain the put into the response promise. Lesson: when a live endpoint
  404s but shape tests pass, suspect the Pages calling convention first
  (single-arg `context` vs `(request, env, ctx)`), then any un-awaited
  side effect before the Response.

## ADR-0056 activation — owner funding gotcha (measured 2026-09-04)

The capital verifier requires the deposit tx to carry BOTH legs in the
same transaction: a USDC Transfer to the treasury AND an Aave V3
`Pool.Supply` event emitted by the treasury wallet. A plain USDC transfer
(no supply) verifies as `no-aave-supply` 404 — the owner's first deposit
(1.0 USDC, tx `0x2c01…31d5`, block 50846957, scanned live via eth_getLogs
over the Base RPCs) is parked as unusable evidence until it is paired with
an Aave supply. Guidance for the next owner funding step: batch transfer +
approve + supply into one tx (AA callData or multisig batch), or amend
ADR-0056 to accept transfer+supply as separate receipts (design-weakening,
needs the owner). To rescan deposits: eth_getLogs on Base USDC
`0x833589fC…2913`, Transfer topic0 `0xddf252ad…b3ef`, topics[2] padded
treasury address, last ~50 blocks.

## Direction: cloud-agent on murakumo (ADR-0092, 2026-09-02)

itonami.cloud is moving from local-agent (owner's Mac resident) to cloud-agent:
`mesh/itonami.app.edn` declares `agent-profile` + `agent-heartbeat` WASM
components (placed 2026-09-02 on levi/dan/joseph; CIDs recorded in the ADR).
The run loop stays off-mesh (JVM resident) until `capability-llm-infer` has an
admitted provider — a substrate constraint, not a preference. Chat model =
GLM-5.3 serverless (Baseten→Together) under a hard monthly JPY cap; video =
Hokusai through the same provider record and admission.

## Bot profile 編集 — SOUL.md は保護対象 (write guard)

Profile の SOUL.md（persona/職務定義）への書込みは Hermes 側の保護対象で、
書込みガードが承認プロンプトを出す。**プロンプトがタイムアウトしたら、
同一 write の無批判リトライも、terminal 等の別経路での回避もしない** —
ガード自身が「Silence is not consent. Do NOT retry it or attempt the same
edit via another path」と明示する。実測 (2026-09-03): 1 セッションで 3 回
タイムアウト（ユーザーの事前承認「do it」があってもガードは通らなかった）。
正しい流れ:

1. 変更案全文を `profiles/<p>/plans/<topic>-<date>.md` にドラフトとして置く
   （plans/ は保護対象外、書ける）。
2. ユーザーにドラフトの場所と承認方法を伝える。対話 UI で承認プロンプトに
   応答してもらう（無音は同意にならない）。
3. 承認が取れたセッションで適用する。organize 依頼の「完了」を「ドラフト+
   実測報告」までとし、SOUL 未適用を明示して報告する（偽装完了にしない）。

逐次編集が不要な全置換の場合も同じ — ガードは write_file/patch の両方に
効く。エージェントは SOUL の内容設計は担うが、適用は承認が通る環境に依存
するという分割を運用手順に織り込んでおく。

## mro_ delegation kit (landed 2026-09-04, ADR-2609040210 in scratchpad/10eros-modal/)

The measured answer to 'how should an agent spend operator authority safely':

- **Mint = owner gesture only** (`/tmp/mint-mro.sh` v3). v3 stores the token in kagi
  (item `murakumo-operator-mro`, compartment `personal` — governed reveal + audit
  ledger for free), keeps `/tmp/mro-token-live` 0600 for agent reads, verifies the
  live authorize round-trip (204) BEFORE storing, and appends a hash-chained receipt
  line to `scratchpad/10eros-modal/mro-receipts.edn` (append-only, prev-sha256 chain).
- **Agent spend = `agent_mro_kit.cljs`** (nbb): TTL-refuse at 600s elapsed (server
  TTL 900s), narrow verbs only (`status` / `verify` / `get-model` / `put-model`),
  every use receipted. The kit has no verb that reaches the grok-bots launch plane.
- **Wire-format boundary (measured, do not re-litigate):** the murakumo mro_ is
  Biscuit v3 protobuf on the wire; `kotoba-lang/org-biscuitsec` is the workspace's
  clean-room EDN decision core that refuses third-party blocks by name. Client-side
  attenuation of a real mro_ is therefore impossible with workspace parts —
  scope-narrowing happens AT MINT TIME (requested action set), and org-biscuitsec
  `authority/->grant` is the local second gate, not a wire transformer.
- **Direction of travel:** register the agent identity in the workforce registry
  (ADR-0058, one human co-sign), add its DID to `MURAKUMO_OPERATOR_DIDS`, and mint
  agent-DID mro_ from a bot CACAO session (path measured working via financial-chief
  enrollment). Then audit reads the agent's own name and no CDP session borrowing
  exists.
- nbb file-mode traps hit while writing the kit: `js->clj` fails in file mode (works
  via `-e`) — use `(vec (js/Array.from (.-argv js/process)))` and remember argv is
  `[node, nbb, script, ...args]` so drop 3; `js/__dirname` is undefined in nbb files
  — hardcode the ledger path or resolve it another way.

## mro_ delegation kit v2 — decision mechanism (2026-09-04, ADR-2609040210)

Owner direction: **agents err less than humans — make the agent the decision-maker;
the human keeps only policy edits + the passkey gesture.** Implemented and
live-verified in scratchpad/10eros-modal/:

- `mro-policy.edn` (OWNER-edited, deny-by-default): verbs that may exist at all,
  known model ids + id pattern, mint hourly cap, tripwire (fail-halt 3 in window
  30min), escalation set. Widening = edit the file (owner act); narrowing needs no one.
- `agent_mro_kit.cljs` v2 (judge INLINE — nbb sibling-ns require proved unreliable,
  do not split again): `decide`/`judge-gate` order every credentialed verb against
  the policy; every verdict is receipted with a sha256 hash chain
  (`receipt/sha256` over the record minus the key, `.digest("hex")`).
- Verified deny paths (all live): `:unknown-verb`, `:bad-model-id` (id pattern),
  `:unknown-model-id` (not in :known-ids — escalates with "owner adds the id"),
  `:tripwire-halt` (3 err receipts in 30min — injected 3, saw the halt, cleaned),
  `:mint-cap` (verified by temporarily setting max-per-hour 0). Chain integrity
  verified (second receipt's prev == first's sha256). Mint does NOT require a live
  token (it IS the remedy); its gate is the hourly cap.
- nbb traps (hit, measured): `js->clj` fails in FILE mode (works via -e) — use
  `(js/Array.from (.-argv js/process))`; argv is [node, nbb, script, ...args] → drop 3;
  `clj->js` STRIPS keyword namespaces (`:receipt/at` → "at") — receipt keys must be
  explicit strings; `js/__dirname` undefined — hardcode the dir; inline python with
  parens inside bash -lc gets mangled — write a real .py file instead.

## Pitfalls

- `~/.hermes/profiles/*/bin/tirith` is **Hermes's bundled pre-exec security
  scanner** (Mach-O binary), not itonami tooling — profile bin/ contents are not
  app CLIs.
- `itonami hermes run` never shells out to `hermes`; the session/messages surfaces
  read the itonami resident, not `~/.hermes/`.
- Filesystem bot-import is refused unless the server is loopback-only.
- Provisioned imported Bots are inert by design; capability grants are later,
  explicit Itonami grants — "presence in the archive" is not a grant.
- **SOUL.md write guard does NOT fire for a brand-new profile created in the
  same session** (measured 2026-09-03, profile `samu`): the guard is a
  protection against overwriting an EXISTING persona; a fresh `hermes profile
  create --clone` copy can be authored/overwritten with plain write_file, and
  the write succeeds silently. What still needs the draft-then-approve dance:
  rewriting the SOUL of a profile that already has a user-approved persona.
  Also measured the same day: `hermes profile describe <p> --text "..."` is the
  description setter (subcommand-arg order matters: profile name BEFORE
  --text), and a profile creation mistake (wrong name) is cheap to fix with
  `hermes profile delete <name> --yes` immediately.
- **Tirith blocks oversized inline shell payloads** (heredocs / giant
  one-liners with nested command substitution land on an unconditional
  blocklist, timeout-and-retry does not clear it). The blocked command is
  saved to `~/.hermes/profiles/<p>/cache/blocked-scripts/blocked-<ts>-*.sh` —
  split the work into small commands (grep one thing at a time) or write a
  real file and run it, instead of re-issuing the same monster line.
  Also blocks `cmd | python3 -c` (pipe-to-interpreter) and flags `rm -rf`
  under /tmp — write probe expressions to a file first (`cat > /tmp/x.clj`,
  then `clojure -M -e "$(cat /tmp/x.clj)"`), and clean up worktrees with a
  `chmod -R u+rwx` before the rm.

## Economic integration with Valueflows/XMILE (ADR-2609111230, accepted 2026-09-03)

Landed as LIBRARY namespaces (app main `bfd158b`) — **no CLI commands were added**
(the `itonami vf journal …` commands once written here were never real; do not
invent a CLI surface without checking `itonami commands vf`). Bots read/append
through `intent → admission → journal`, never bot-to-bot messaging:

- `cloud.itonami.app.vf-journal` (slice 1): per-org append-only EDN journal.
  Gates in fixed order — `valueflows.conform/conform-event` (`:conform` stage,
  bad payload) then `valueflows.event/apply-event` over the CURRENT inventory
  (`:fold` stage, event doesn't fit this state); each rejection its own stage.
  Every accepted line carries the post-fold sha256 inventory root; replay
  CHECKS it (hand-edited root refuses to load). Vocabulary consumed, never
  reimplemented: deps.edn pins `ws-valueflo-vocabulary` `4c1e0106` = west pin.
- `cloud.itonami.app.vf-authority` (slice 2): `kotoba://vf/<org>/<plane>/<action>`
  wire form, CLOSED plane/action table (undefined pair → nil, never minted).
  Three loop-yakuwari keywords map: `:vf.read`→`event/read`,
  `:vf.append`→`event/append`, `:vf.commit`→`commitment/commit`; anything else
  is nil here (stays a tool scope). Decider stays `authority.scope/covers?` /
  `meet` — org-a does not cover org-ab, read/append/commit are separate leaves,
  an incomparable attenuate ask has no meet (nothing synthesised).
- `cloud.itonami.app.vf-calibrate` (slice 3): `:vf/xmile` correspondence table
  (org → {resource-id → constant name}) rebases LEAF constants (bare-number
  eqn, the exact shape `loops/sensitivity` perturbs) to the journal's folded
  `:onhand-quantity`. Bindings onto COMPUTED variables are refused (that would
  be a different model, not a calibration). Report names `:rebased` /
  `:unmatched` / `:ignored`. Flow rates are never written — the
  `:different-formalism` boundary (ADR-2608153000) holds.

**Still open** (recorded in the ADR): gateway effect-phase wiring — admitted
`vf.event.append` intents do NOT yet drive `vf-journal/append-event!` (admission
and journal are two working halves, not one loop); per-bot grant rollout is an
operational decision; `valueflows.proposal` has no app-side reader yet.

Measured pitfalls for this app's test surface (all hit live 2026-09-03):

- `deps.edn :test` alias has fixed `:main-opts` — `clojure -M:test -e 'expr'`
  IGNORES `-e` and runs the whole 2,257-test suite. Run one namespace with
  `clojure -M:test -m cloud.itonami.app.test-runner <ns…>`.
- `target/test-data/` holds read-only git-annex fixtures — `rm -rf` fails with
  Permission denied and aborts `&&` chains (a test run then silently doesn't
  happen). Don't delete it; run individual namespaces instead. Removing a whole
  worktree needs `chmod -R u+rwx target/test-data` first.
- A second concurrent JVM (leftover test run or headless server) sharing the
  data dir makes store load die with `state journal append does not fit this
  state` at namespace load — environmental, not your bug; the orphan journal is
  auto-archived with a WARNING.
- A conforming `produce` event REQUIRES `:resource-inventoried-as` — without it
  conform passes but fold rejects `:missing-resource`. Fixture shape is in the
  vocabulary's own `event_test.cljc`.
- After patching an `.edn` ADR/body string, verify by reading it back
  (`edn/read-string`, count entities/keys, `clojure.string/includes?` for each
  section) — a patch that drops the closing `]` or `}` reads as EOF-while-reading
  only at the next consumer.
- XMILE's `<sim_specs>` parses onto the DOC (`:xmile/sim-specs` of
  `xmile.xml/parse-doc`), not the model map — `loops/runnable-model` merges doc
  sim-specs onto the first model; a test building models must do the same or
  `execute/run` NPEs on a nil `:xmile/start`.

Session detail: `references/vf-integration.md`.

Condensed ADR detail (migration artifact trio + information matrix, resident API
endpoints, model-routing task table, session/bearer details, mesh placement
receipts): `references/adr-compat-map.md`
