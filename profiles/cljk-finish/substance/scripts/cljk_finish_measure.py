#!/usr/bin/env python3
"""cljk-finish measure — read-only, appends to workspace ledger.

Measures (per west checkout that exists on disk under orgs/, plus superproject
scripts/):
  strlit-oldext : string literals in .cljk files naming a ".cljs" path whose
                  target does NOT exist on disk (rename follow-through residue;
                  the skill rule says fix PATHS, not assertions).
  bb-dead       : *.bb files whose basename is referenced nowhere else
                  (in-repo scan + hermes profile cron dirs + superproject scripts).

Output lines (machine-readable, one per finding):
  CANDIDATE\t<repo>\t<kind>\t<n>
  NONE            (measured clean, 0 candidates)
  REFUSED <why>   (could not measure - never report that as clean)
Exit: 0 on a completed measurement (including NONE), 2 on REFUSED.
Appends one JSON line per run to <profile>/workspace/cljk-finish-ledger.jsonl.
"""
import os, sys, json, glob, time, re, subprocess

ROOT = os.path.expanduser("~/github/com-junkawasaki")
PROFILE = os.path.expanduser("~/.hermes/profiles/cljk-finish")
LEDGER = os.path.join(PROFILE, "workspace", "cljk-finish-ledger.jsonl")
PRUNE = {"node_modules", ".git", ".nbb", "target", "dist", "build"}

def walk_files(base):
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in PRUNE]
        out.extend(os.path.join(dirpath, f) for f in filenames)
    return out

def repos_on_disk():
    repos = []
    orgs = os.path.join(ROOT, "orgs")
    if not os.path.isdir(orgs):
        return None
    for org in sorted(os.listdir(orgs)):
        od = os.path.join(orgs, org)
        if not os.path.isdir(od):
            continue
        for repo in sorted(os.listdir(od)):
            rd = os.path.join(od, repo)
            if os.path.isdir(os.path.join(rd, ".git")) or os.path.isfile(os.path.join(rd, ".git")):
                repos.append(rd)
    return repos

def main():
    repos = repos_on_disk()
    if repos is None:
        print("REFUSED orgs/ not readable"); sys.exit(2)
    # extra reference sources for bb liveness (outside the repo itself)
    ext_refs = set()
    for pat in [os.path.join(ROOT, "scripts"),
                os.path.expanduser("~/.hermes/profiles/*/cron"),
                os.path.expanduser("~/Library/LaunchAgents")]:
        for d in glob.glob(pat):
            for f in walk_files(d):
                ext_refs.add(os.path.basename(f))
            for f in glob.glob(os.path.join(d, "*")):
                if os.path.isfile(f):
                    try:
                        txt = open(f, errors="ignore").read()
                    except Exception:
                        continue
                    for m in re.findall(r"[\w./-]+\.bb\b", txt):
                        ext_refs.add(os.path.basename(m))

    findings = {}  # repo -> {kind: [files]}
    scanned = 0
    for rd in repos:
        files = walk_files(rd)
        scanned += 1
        # strlit-oldext: .cljk string literals naming a .cljs path that is stale
        for f in files:
            if not f.endswith(".cljk"):
                continue
            try:
                txt = open(f, errors="ignore").read()
            except Exception:
                continue
            for m in re.findall(r'"([^"\n]*\.cljs)"', txt):
                if m.startswith(("http://", "https://", "file://")):
                    continue
                # resolve the literal against the repo root; stale if missing
                cand = m if os.path.isabs(m) else os.path.join(rd, m)
                if not os.path.exists(cand) and not os.path.exists(cand.replace(".cljs", ".cljk")):
                    findings.setdefault(rd, {}).setdefault("strlit-oldext", []).append(
                        (os.path.relpath(f, rd), m))
                break  # one stale-literal finding per file is enough
        # bb-dead: *.bb files referenced nowhere (repo basenames + external refs)
        bbs = [f for f in files if f.endswith(".bb")]
        if bbs:
            baserefs = {os.path.basename(f) for f in files} - {os.path.basename(f) for f in bbs}
            refpool = baserefs | ext_refs
            for f in bbs:
                if os.path.basename(f) not in refpool:
                    findings.setdefault(rd, {}).setdefault("bb-dead", []).append(
                        (os.path.relpath(f, rd), ""))

    seq = 0
    if os.path.exists(LEDGER):
        with open(LEDGER) as fh:
            for line in fh:
                try:
                    seq = max(seq, json.loads(line).get("seq", 0))
                except Exception:
                    pass
    entry = {
        "seq": seq + 1,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repos_scanned": scanned,
        "candidates": {os.path.relpath(r, ROOT): {k: v for k, v in kinds.items()}
                        for r, kinds in sorted(findings.items())},
        "candidate_repos": len(findings),
    }
    with open(LEDGER, "a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    for r, kinds in sorted(findings.items()):
        for kind, fl in sorted(kinds.items()):
            print(f"CANDIDATE\t{os.path.relpath(r, ROOT)}\t{kind}\t{len(fl)}")
    if not findings:
        print("NONE")
    sys.exit(0)

if __name__ == "__main__":
    main()
