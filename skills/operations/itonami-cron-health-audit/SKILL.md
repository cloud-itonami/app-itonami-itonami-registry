---
name: itonami-cron-health-audit
description: Audit measured Hermes bot cron health across caller-selected profiles and distinguish guarded skips, transient infrastructure errors and persistent failures.
metadata: {"hermes": {"version": "0.1.0", "author": "cloud-itonami", "source": "https://github.com/cloud-itonami/app-itonami-bot-fleet/tree/b6120bb7214ac92b14e81c865c34048b14e5f762", "compatibility": {"hermes": "*", "desktop": "*"}}}
---

# Itonami cron health audit

Use the owning repository's evidence collector with a bounded time window. The source of this procedure is the pinned cron-health profile listed in itonami.json; its script remains owned by ao-bot-fleet. This skill does not install that script or grant access to profiles.

1. Enumerate only the caller-selected profiles. Exclude backup copies. Read job definitions and per-job model/provider overrides; a profile default alone does not describe the job's route.
2. Run the selected collector once. Preserve observation time, corpus size and its classification. A missing collector, REFUSED result or failed measurement is unmeasured. Do not substitute a guessed score or a second implementation.
3. For a candidate failure, correlate the scheduled job with its execution record, scheduler log and final report. A listed schedule proves a definition; a manual run does not prove that scheduling works. Old failure streaks may disagree with later scheduler success.
4. Separate intentional spend-guard skips, provider quota/capacity errors, and restart/overload collateral from persistent script, connection or lock failures. Confirm the named script currently exists before acting on an old script-not-found error.
5. Report one consequential evidenced finding, with source references and unresolved checks. Write only to the caller-authorized result path. Honor the caller's notification intent when state is unchanged.

Do not pause, move, recreate or resume jobs as part of an audit. Any repair or routing change is separate work under the target owner's policy. Do not copy credential values between profiles.
