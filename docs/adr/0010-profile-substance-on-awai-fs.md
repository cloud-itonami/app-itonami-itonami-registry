# ADR 0010 Bot profile substance storage on AwaiFS/AwaiVol

Status: proposed, 2026-11-14. Amends ADR 0003; transitions ADR 0002 §1
commit-pin format for profiles to CID pins on cutover.

Owner decision (2026-11-14, recorded on JUN-1070): the substance of itonami
bot profiles lives on AwaiFS / AwaiVol, not on GitHub.

## Context

- ADR 0003 stores profile definitions as git pins: each `profile` entry pins
  one commit of an owning GitHub repository with per-file sha256
  (currently 899 profiles). State goes to a DataLad annex or data plane,
  secrets to the credential store only.
- JUN-1070 (Backlog, on hold since 2026-11-09) keeps registry-first; the
  rev.2 physical monorepo is a future option only.
- AWAI-2795 already persists runtime state, job results and manifests on
  AwaiVol (`/Volumes/AwaiVol/itonami-*-v1`) with byte readback.

## Decision

1. **Substance location.** The definitions layer (`SOUL.md`, `profile.yaml`,
   `config.yaml`, `cron/jobs.json`, `skills/`, `scripts/`, `itonami.edn`,
   `yakuwari.edn`) is stored as immutable content-addressed objects on
   AwaiFS / AwaiVol (Pack/CAR per the Otehon storage contract), addressed
   by CID.
2. **Registry holds pointers only.** A `profile` entry maps id to CID plus
   payload sha256 and byte size. No file copies, and no new GitHub
   commit pins for substance after cutover.
3. **State and secrets unchanged.** State keeps the ADR 0003 destinations
   (annex / data plane, including the AwaiVol runtime directories);
   secrets stay in the credential store only and never enter AwaiFS
   objects or the registry.
4. **Migration with readback.** PoC with one profile, then the bulk 899
   with byte readback each. Owning GitHub repositories are frozen or
   archived only after readback; old commit pins stay until cutover is
   verified, so every profile keeps a working resolution throughout.
5. **Tooling follows.** `scripts/add_profile.py`, `validate.py` and
   `build_index.py` gain CID-pin support (schema revision); new
   registrations after cutover use the CID form.

## Consequences

- ADR 0002 §1's commit pin plus `sha256-tree` is replaced by the CID pin
  for profiles. The installer resolves substance through the AwaiFS
  gateway and verifies payload checksum before use.
- GitHub stops being the home of profile substance; no new substance
  commits land in owning repositories.
- Registration still grants nothing: accounts, grants and schedule are
  rebound by the installer, and cron arrives disabled (ADR 0002).

## PoC evidence (2026-11-14)

- Profile `itonami` (65 files) materialised from git objects at pinned
  commit `57ff9f34` — never the working tree — and written to
  `/Volumes/AwaiVol/itonami-profile-poc-JUN-1070-v1/itonami/` with a
  `poc-manifest.json` of per-file sha256.
- All 65 files match the registry `manifest.json` hashes; AwaiVol
  readback of all 65 files is byte-identical. No registry change was
  needed for the PoC; existing profiles and state were untouched.

## Not yet verified

- The AwaiFS CID codec details for profile payloads (PoC used POSIX
  files plus a sha256 sidecar, not Pack/CAR CIDs).
- Scheduler and runtime binding to AwaiFS substance (confirmed through
  AWAI-2795 receipts, not through this ADR alone).
