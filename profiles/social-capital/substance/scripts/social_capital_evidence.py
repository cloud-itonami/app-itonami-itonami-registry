#!/usr/bin/env python3
"""social-capital evidence: measure the pipeline inputs, read-only.

Emits MEASURE<TAB>key<TAB>value lines, appends to
workspace/social-capital-evidence.jsonl. Missing inputs are UNMEASURED.
Nothing here writes outside the profile workspace.
"""
import json, subprocess, os, sys, time, glob

PROFILE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.join(PROFILE, "workspace")
LEDGER = os.path.join(WS, "social-capital-evidence.jsonl")
ROOT = "~/github/com-junkawasaki"

os.makedirs(WS, exist_ok=True)
out = []

def m(k, v):
    out.append((k, str(v)))
    print("MEASURE\t%s\t%s" % (k, v))

def sh(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None

def count_lines(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return None

# --- superproject / proposal state ---
m("root-head", sh(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"]) or "UNMEASURED")
m("proposal-file", "present" if os.path.exists(ROOT + "/90-docs/business/social-capital-proposal-20260914.md") else "MISSING")
m("adr-file", "present" if os.path.exists(ROOT + "/90-docs/adr/2609141203-social-capital-ledger.edn") else "MISSING")

# --- sc.core repo existence (R0 gate: not scaffolded until go) ---
m("sc-repo", "present" if os.path.exists(ROOT + "/orgs/kotoba-lang/social-capital") else "NOT-SCAFFOLDED")

# --- pipeline input planes (read-only counts) ---
CHECKOUTS = {
    "hyakka": ROOT + "/orgs/network-awai/app-hyakka",
    "aozora": ROOT + "/orgs/network-awai/app-aozora",
    "moyoshi": ROOT + "/orgs/network-awai/actor-moyoshi",
    "credits-engi": ROOT + "/orgs/cloud-itonami/credits",
    "inga": ROOT + "/orgs/kotoba-lang/inga",
    "shinkansen": ROOT + "/orgs/kotoba-lang/shinkansen",
}
for k, path in CHECKOUTS.items():
    m("head-" + k, sh(["git", "-C", path, "rev-parse", "--short", "HEAD"]) or "UNMEASURED")

# --- moyoshi settle outputs (existing social/mint evidence, if any committed seeds) ---
moy = CHECKOUTS["moyoshi"]
m("moyoshi-methods", str(len(glob.glob(moy + "/src/moyoshi/methods/*"))) + " files")

# --- ledger self-check ---
last = None
rows = 0
if os.path.exists(LEDGER):
    rows = count_lines(LEDGER)
    try:
        with open(LEDGER) as f:
            for line in f:
                if line.strip():
                    last = line.strip()
    except Exception:
        last = None
m("ledger-rows", rows)
m("ledger-last", (last[:160] if last else "EMPTY"))

row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "measures": dict(out)}
with open(LEDGER, "a") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
print("LEDGER\t" + LEDGER)
print("SCANNED\t%d" % len(out))
