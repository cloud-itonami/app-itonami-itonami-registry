---
name: hermes-fleet-cron-health
description: Use when auditing Hermes bot profiles or cron fleet health.
---

# Hermes bot fleet / cron health audit

## Inventory (workspace root = ~/.hermes/profiles/)

- Profiles: count dirs under `~/.hermes/profiles/`. Cron jobs: parse `~/.hermes/profiles/<p>/cron/*.json` — each file is `{"jobs": [...]}` with per-job fields `enabled`, `state`, `paused_at`, `last_status`, `last_error`, `failure_streak`, `last_run_at`, `next_run_at`, `schedule_display`, `repeat.completed`, `last_dispatch` (has `scheduled_at`/`dispatched_at`), `deliver`.
- Exclude `*.bak-*` profile dirs (user keeps backup clones; they inflate counts).
- `cronjob_manage` only sees the CURRENT profile's jobs — cross-profile audit must read the JSON files directly.
- Gateway profiles are the ones with a live process: `ps aux | grep 'hermes_cli.main.*gateway run'` and extract `--profile <name>`. A profile with cron but no gateway means its jobs fire only if some supervisor loop starts it.

## Scoring (measured recipe)

Job-level: last_status ok/error/delivery_failed; failure_streak>0 multiplies risk; never-run jobs are NORMAL when created <7 days ago with a future next_run_at (weekly/new) — only never-run AND old AND next_run past = stalled. Profile score: ok-rate over ran jobs, minus streak*0.03 (cap 0.3), minus stalled fraction*0.4, minus delivery_failed fraction*0.2, minus 0.1 if no live gateway.

Error classification by last_error substring: "Gateway shutdown (post-interrupt)" = collateral of a gateway restart wave (batch, self-heals next fire); "HTTP 429" = capacity (reschedule off the busy slot) — but "429 daily free quota exhausted" is QUOTA exhaustion (recurs every UTC day until the tier/key changes, reschedule won't fix); "HTTP 402 requires more credits / would exceed available credits" = billing exhausted on the paid route (a tier/top-up decision, not scheduling); "truncated" = response too big (lower frequency); "Connection error" on a NEW profile's first runs = missing API keys in the profile's `.env` (config.yaml alone does not carry keys — copy the key lines from the template profile); "TERMINAL_CWD read lock" = two cron jobs sharing a workdir (separate workdirs); "REFUSED" = script-level precondition, not scheduling. **"drift_skip" / "Skipped to prevent unintended spend: global" is a SPEND-GUARD, not a fault** — the job intentionally skipped to avoid token cost and fires again next tick. On a price-aware fleet 1/4 to 1/3 of "error" jobs are this class; separate it out BEFORE computing error rate or you over-report a healthy fleet as ~20-30 errors when the true break-count is single digits. See references/error-classification.md for the full bucket table.

Host discriminator: loadavg/core-ratio. `sysctl -n vm.loadavg` (first value) against `sysctl -n hw.ncpu`. Ratio >3 = host overload; a wave of identical interrupt/shutdown errors at that point is one host event, not N bot failures. Do not reschedule for it.

Per-job `provider`/`model`/`base_url` (+`provider_snapshot`/`model_snapshot`) fields in jobs.json OVERRIDE the profile config default — a fleet model switch that only changes profile configs leaves the pinned majority untouched. Before any switch, tabulate jobs by their own model/provider fields (inherit vs pinned) and count fires/day from each schedule expr (minute/hour multipliers); that table is the real switch scope.

last_error fields are live snapshots that mutate between scans (jobs re-fire while you audit) — re-run the scan right before finalizing counts, and don't quote a scan taken more than a few tool calls ago.

Caveat on script-not-found errors: validate the script currently exists (`ls <profile>/scripts/<name>.py`) before trusting a "Script not found" line — it may be a stale snapshot from before the script was placed, so the fault is already healed and needs only a re-fire to confirm.

## Tool-backend topology check (FIRST, before any desktop/profile diagnosis)

When the user reports a Hermes desktop or profile error, do NOT assume your file tools run on the same machine as the desktop app. Determine the topology first, in one call: `hostname; id -un; echo $HOME` via terminal AND `os.environ['HOME']` via execute_code — they can disagree. If the paths in the user's error stack (e.g. `/Users/<otheruser>/.hermes/...`) do not exist from your shell, your terminal backend SSHes into a different host: say so explicitly, report which paths are unreachable, and hand the user the exact local commands (grep over `~/.hermes/profiles/*` for the failing bot's URL/name, `hermes cron list`) instead of concluding from empty greps.
- A grep returning 0 hits on an unreachable path is NOT evidence of absence — it is unmeasured. Run one `ls -d <path>` control first; only a pass on an existing dir counts.
- vision_analyze and similar file-path tools reject non-ASCII paths (Japanese screenshot filenames fail with an ASCII-only error). Ask the user for an ASCII-safe copy or the image content instead of retrying the same call.
- Browser/PTY-based backends may be routed elsewhere again — one failed browser_exec with empty stdout is not proof the tool class is broken; verify via the workspace path it echoes before generalizing.

## Report format (owner expects)

対象 corpus / 追加 datoms / 台帳 seq / 異常の有無. Lead with totals (profiles, jobs, ok rate), then score tiers, then error classes with counts, then concrete per-job fixes.

## Provider switch on a 401 wave (executed 2026-09-16, 29 profiles)

When a fleet-wide `HTTP 401: Invalid credential` wave occurs, inspect provider names, `key_env` names, and credential-presence metadata without reading or copying secret values. Keep inference on Murakumo/Mishima and `fallback_providers: []`; if the configured key is missing or invalid, stop and ask the owner to repair it through the approved secret store. Do not switch providers, copy tokens between profile `.env` files, or refire disabled jobs.

## Historical provider-switch notes

The former Kotoba / external-provider switch procedures below have been retired. They are not an operational runbook. Current owner policy permits Murakumo/Mishima only with `fallback_providers: []`; do not edit job providers, resnapshot jobs to another provider, or refire disabled jobs. On authentication, capacity, quota, or vision errors, inspect logs without exposing secret values, stop the affected work, and report the specific blocker to the owner.

## Profile model-section auth and budget pitfalls

- A profile `config.yaml` whose `model:` section carries `provider` + `base_url` must also carry the matching `key_env` in `model:` and the Murakumo provider entry. Check that the configured variable exists without reading its value. Keep Murakumo/Mishima and `fallback_providers: []`; credential repair belongs to the owner-approved secret store, never copying secrets between profiles.
- An agent-type cron job with no `run_budget_seconds` can run too long; set a bounded budget consistent with the job. Do not use quota exhaustion as a reason to switch to a weaker or external fallback model. Stop and report when Murakumo cannot serve the configured Mishima request.

## Historical quota note

The prior Kotoba free-tier measurements are retained only as historical context. Do not use them to trigger a provider switch or mass re-fire. The current route is Murakumo/Mishima with `fallback_providers: []`; when capacity or quota blocks work, stop and report.
