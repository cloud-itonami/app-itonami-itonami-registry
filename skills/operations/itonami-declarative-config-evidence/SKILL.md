---
name: itonami-declarative-config-evidence
description: Evaluate owner configuration against explicit policy literals and retain satisfied, violated and unverified verdicts.
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-assistant/tree/5c803ed4fa159742e11e2d050dc449b58c7ff233
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-declarative-config-evidence

Resolve the current inspection runtime and policy owner (the source procedure references tenken). Bind the selected config files and the exact rule literals, policy nature and fail-closed behavior. The registry carries no organization-wide storage prohibition.

Use the real parser for the declared JSONC/TOML format and the owner's normalized model. An unreadable config is unverified, not an empty compliant config. Preserve each verdict's rule and reason; a reason-free satisfied assertion is not evidence.

Record SCANNED, VIOLATED, UNVERIFIED and SUMMARY outcomes, the input revision and native exit status. In the documented owner protocol, exit 0/1/2 distinguishes satisfaction, violations and unverified inspection; confirm the installed runner contract before interpreting it.

Propose a targeted owner-scoped correction only from fresh verdicts. Inspection is not permission to remove databases, bindings, secrets or services. Recheck the policy before using a historical runbook example.

Pinned derivation inputs are in itonami.json and catalogs/sources.json; owner runtimes and profiles are referenced, not imported.
