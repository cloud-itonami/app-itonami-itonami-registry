---
name: oppai-producer-hourly
description: Use when running the hourly oppai.fans Producer tick.
---

# oppai-producer hourly run

> This skill is reference material; it does not authorize image generation, producer submission, deployment, or publication. Perform those actions only under explicit owner approval. Use Murakumo/Mishima only and `fallback_providers: []`.

Repo worktree: `~/github/wt/<agent-or-bot>/<task>/fans-oppai`; source checkout: `~/github/network-awai/fans-oppai`. Receipts: `~/github/workspaces/<agent-or-bot>/<task>/oppai-producer/<YYYYMMDDTHHZ>/receipt.json`. Read receipts FIRST; generated/submitting/uncertain block new generation; deployed does not.

## Steps
1. `git status` + `git fetch origin`; read docs/support.md if unsure.
2. Support inbox via R2: `sh ~/.local/state/oppai-producer/scripts_run/r2reader_oppai.sh feedback/ 20` (same for site-errors/); fetch single keys with r2get_oppai.sh. Old D1 is historical only.
3. MCP `producer_audit_posts` limit 20 → dupes/phrases (bias 'waist up portrait'/'soft daylight' 20/20 still open).
4. Live version: repo-local `node_modules/.bin/wrangler deployments list --config wrangler.jsonc --json` (NOT npx — cron blocks it on threat scan). Newest entry with one 100% version is expected_version.
5. Generate (only if this UTC hour has no receipt): `cd worktree && /opt/homebrew/bin/kbb --backend sci --classpath scripts:src scripts/producer_tick.cljk --balanced`. Exactly one submit per hour.
6. Decode: copy scripts_run/decode_21Z.py pattern (response.image is a `data:image/png;base64,` URI — strip prefix before b64decode; decode_11Z.py may not handle it). Write PNG, sha256, confirm it equals response.artifact.sha256. Vision-review the actual PNG; reject garbled text banners / UI / dupes / blank. Atomically update receipt (script file + os.replace). Keep state='generated' after review (publish gate in scripts/producer_publish.cljk only accepts generated/deployed/published + reviewed true; setting state='reviewed' fails 'A reviewed, zero-price PNG receipt is required' — fix by reverting state, no regen).
7. MCP `producer_publish` {hour, sha256, expected_version} → deployed+commit+version. Then `producer_verify_post` {hour} → require checks all true. Keep state=deployed; published needs real browser/public fetch (browser policy denies oppai.fans; do not bypass).

## Pitfalls
- Use the configured Murakumo vision model through the approved `vision_analyze()` route. If the configured Mishima model returns `invalid-research-request` because it is text-only, stop and report; do not upload images to OpenRouter or another provider or seek a second-model review.
- Shared-workflow race: while you vision-review, Codex may set the same-hour receipt generated→deployed (title/tags/commit/version appear). Your reject/review scripts must assert the expected state and skip on mismatch — never overwrite a deployed receipt; do not roll back the newer live release.
- Fresh task worktrees must use the canonical `~/github/wt/<agent-or-bot>/<task>` location. Install dependencies through the repo-supported package workflow and configure explicit classpaths; do not create symlinks into another checkout or work under `/private/tmp`.
- Cron blocks `python3 -c`, `node -e`, `npx wrangler`, execute_code. Write script files under scripts_run/ and run `python3 file.py`; wrangler via repo-local binary; parse JSON with read_file or jq.
- ⚠ 2026-09-19: terminal tool returned empty stdout for every command; workaround = redirect output to a task scratch file under `~/github/workspaces/<agent-or-bot>/<task>` and read it back.
- Install worktree dependencies through the repository-supported package workflow; do not symlink another checkout's dependencies.
- 2026-09-20 09Z: `wrangler deployments list` without `--config wrangler.jsonc` can find an unrelated config; always pass the project config. Historical producer_publish failures are not permission to retry a submission.
- Historical external-model test results are retained for provenance only. They are not approved routes; use Murakumo vision or stop and report.
