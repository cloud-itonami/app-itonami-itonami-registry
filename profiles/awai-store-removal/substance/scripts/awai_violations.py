#!/usr/bin/env python3
"""Evidence script for awai-store-removal bot.
Runs verify-awai-state-store-policy.cljk, prints MEASURE lines + next-work pick.
Read-only: never mutates git state. Exits 2 when measurement itself failed."""
import json, os, subprocess, sys, datetime, re

# 2026-10-02: superproject checkout moved to root/ (top-level layout is a stale
# leftover: .git replaced by a git-annex stub dir, orgs/ nearly empty). Scanning
# the old root gave SCANNED 1 / false ALL-CLEAN. Real superproject = <base>/root.
ROOT = "~/github/com-junkawasaki/root"
LEDGER = os.path.expanduser("~/.hermes/profiles/awai-store-removal/workspace/removal-ledger.jsonl")
VERIFY = os.path.join(ROOT, "scripts/verify-awai-state-store-policy.cljk")

# Worktree/scratch checkout dirs owned by other bots or one-off tasks are
# violation-visible but not our landing targets. Exclude from PICK (keep in
# violations_detail so the count stays honest).
WORKTREE_RE = re.compile(r"(^|/)(\.worktrees/|[^/]*(-wt$|-wtx$|wtx/)|[^/]*-\d{8}(-[a-z0-9-]+)?$|[^/]*site-verify$)")

def out(*a):
    print(*a)

def main():
    try:
        r = subprocess.run(
            ["kbb", "--backend", "sci", VERIFY, "--root", "."],
            cwd=ROOT, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        out("STATUS\tREFUSED\tverify timeout 240s")
        return 2
    if r.returncode not in (0, 1):
        out("STATUS\tREFUSED\tverify rc=%s stderr=%s" % (r.returncode, (r.stderr or "")[:200]))
        return 2
    violations = {}
    scanned = None
    for line in (r.stdout or "").splitlines():
        parts = line.rstrip("\n").split("\t")
        if parts[0] == "SCANNED":
            scanned = parts[1]
        elif parts[0] == "VIOLATION" and len(parts) >= 3:
            path, kinds = parts[1], parts[2]
            repo = path[len(ROOT):].lstrip("/").split("/wrangler")[0]
            violations[repo] = kinds
        elif parts[0] == "VIOLATIONS":
            out("MEASURE\tviolations\t%s" % parts[1])
    if scanned is None:
        out("STATUS\tREFUSED\tno SCANNED line")
        return 2
    out("MEASURE\tscanned\t%s" % scanned)
    out("MEASURE\tviolations_detail\t%s" % json.dumps(violations, ensure_ascii=False))

    # landed = latest ledger row for the repo carries a merge sha.
    # design/mapped/started-incomplete rows do NOT clear a repo (2026-09-19:
    # script used rec.get("merge") which never exists -> every row counted as
    # landed -> false ALL-CLEAN while 9 real violations stood).
    done_land = {}
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("repo"):
                        sha = None
                        for k in ("merge", "merge_sha"):
                            v = rec.get(k)
                            if isinstance(v, str) and re.fullmatch(r"[0-9a-f]{7,40}", v.strip()):
                                sha = v.strip()
                                break
                        if sha:
                            done_land[rec["repo"]] = sha
                except Exception:
                    pass
    out("MEASURE\tledger_landed\t%d" % len(done_land))

    if not violations:
        out("STATUS\tALL-CLEAN\tno violation measured")
        return 0

    # next pick: mainline violation (worktree/scratch dirs excluded from PICK),
    # skip archived manimani. The measured VIOLATION rows are authoritative;
    # ledger_landed is reported only (a stale ledger must not hide a violation).
    picks = [k for k in sorted(violations)
             if "manimani" not in k and not WORKTREE_RE.search(k)]
    if not picks:
        out("STATUS\tNO-PICK\tunlanded violations exist but none is a mainline repo "
            "(worktree-only or archived); real violations = %s" %
            json.dumps(violations, ensure_ascii=False))
        return 1
    next_repo = picks[0]
    out("PICK\t%s\t%s" % (next_repo, violations[next_repo]))
    out("MEASURE\tremaining\t%d" % len(picks))
    return 0

sys.exit(main())
