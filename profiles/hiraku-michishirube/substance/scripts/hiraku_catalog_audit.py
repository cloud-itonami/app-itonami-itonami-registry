#!/usr/bin/env python3
"""hiraku-michishirube: measure the 道しるべ catalog.

Reads data/catalog.json + data/axes.json from the ao-hiraku checkout, probes the
links that were checked longest ago, and reports coverage per (axis, stage).
Emits MEASURE<TAB>key<TAB>value and GAP<TAB>axis<TAB>stage<TAB>alive<TAB>total
lines, appends one row to workspace/michishirube-ledger.jsonl.

Writes only inside the profile workspace. The catalog itself is never edited
here; changes are proposals (workspace/proposals/*.json) for the operator.
"""
import json, os, sys, time, urllib.request, urllib.error

PROFILE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.join(PROFILE, "workspace")
LEDGER = os.path.join(WS, "michishirube-ledger.jsonl")
LINK_STATE = os.path.join(WS, "link-state.json")
def _find_repo():
    """Where data/ lives: $HIRAKU_REPO, the ao-hiraku checkout, else the copy
    bundled in the profile itself (how a peer node that runs this bot by
    bundle CID, without the checkout, gets the catalog)."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for c in (os.environ.get("HIRAKU_REPO"), "~/github/cloud-itonami/ao-hiraku", here):
        if c and os.path.isfile(os.path.join(os.path.expanduser(c), "data", "catalog.json")):
            return os.path.expanduser(c)
    return here


REPO = _find_repo()
PROBES_PER_TICK = int(os.environ.get("HIRAKU_PROBES", "10"))
RECHECK_SECONDS = 7 * 24 * 3600
UA = "Mozilla/5.0 (compatible; itonami-hiraku-linkcheck/0.1; +https://itonami.cloud)"

os.makedirs(os.path.join(WS, "proposals"), exist_ok=True)


def m(k, v):
    print("MEASURE\t%s\t%s" % (k, v))


def load(name):
    with open(os.path.join(REPO, "data", name), encoding="utf-8") as f:
        return json.load(f)


def probe(url):
    """Return (status, detail). status: alive | dead | error."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                return "alive", "%s %d" % (method, r.status)
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue  # some sites refuse HEAD; retry with GET
            return ("dead" if e.code in (404, 410) else "error"), "%s %d" % (method, e.code)
        except Exception as e:  # DNS, TLS, timeout
            return "error", "%s %s" % (method, type(e).__name__)
    return "error", "no-method"


try:
    axes = load("axes.json")
    catalog = load("catalog.json")
except Exception as e:
    m("catalog", "UNMEASURED %s" % type(e).__name__)
    sys.exit(1)

entries = catalog["entries"]
try:
    with open(LINK_STATE, encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    state = {}

# --- probe the links checked longest ago ---
now = time.time()
due = [e for e in entries if e.get("url") and now - state.get(e["id"], {}).get("ts", 0) > RECHECK_SECONDS]
due.sort(key=lambda e: state.get(e["id"], {}).get("ts", 0))
probed = []
for e in due[:PROBES_PER_TICK]:
    status, detail = probe(e["url"])
    state[e["id"]] = {"ts": now, "status": status, "detail": detail, "url": e["url"]}
    probed.append((e["id"], status, detail))
    print("PROBE\t%s\t%s\t%s" % (e["id"], status, detail))
with open(LINK_STATE, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=1)


def alive(e):
    # phone-only entries are counted alive: they cannot be probed by HTTP and
    # are re-checked by the operator against safety.json.
    if not e.get("url"):
        return bool(e.get("phone"))
    return state.get(e["id"], {}).get("status") == "alive"


# --- coverage per (axis, stage) ---
cells = []
for a in axes["axes"]:
    for s in axes["stages"]:
        inside = [e for e in entries if a["id"] in e["axes"] and s["id"] in e["stages"]]
        cells.append({"axis": a["id"], "stage": s["id"],
                      "total": len(inside), "alive": sum(1 for e in inside if alive(e))})

with_url = [e for e in entries if e.get("url")]
measured = [e for e in with_url if e["id"] in state]
alive_n = sum(1 for e in with_url if state.get(e["id"], {}).get("status") == "alive")
dead = sorted(e["id"] for e in with_url if state.get(e["id"], {}).get("status") == "dead")
errs = sorted(e["id"] for e in with_url if state.get(e["id"], {}).get("status") == "error")

m("entries", len(entries))
m("links-measured", "%d/%d" % (len(measured), len(with_url)))
m("links-alive", alive_n if measured else "UNMEASURED")
m("links-dead", ",".join(dead) or "none")
m("links-error", ",".join(errs) or "none")
m("cells", len(cells))
m("cells-empty", sum(1 for c in cells if c["total"] == 0))
m("cells-no-alive", sum(1 for c in cells if c["alive"] == 0))
m("free-ratio", "%.2f" % (sum(1 for e in entries if e.get("cost") == "free") / max(1, len(entries))))
langs = sorted({l for e in entries for l in e.get("langs", [])})
m("langs-covered", ",".join(langs))
m("langs-missing", ",".join(l for l in axes["languages"] if l not in langs) or "none")

# weakest cells first: no alive entry, then fewest total
cells.sort(key=lambda c: (c["alive"], c["total"], c["axis"], c["stage"]))
for c in cells[:8]:
    print("GAP\t%s\t%s\t%d\t%d" % (c["axis"], c["stage"], c["alive"], c["total"]))

row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "entries": len(entries),
       "links_measured": len(measured), "links_with_url": len(with_url), "links_alive": alive_n,
       "dead": dead, "error": errs, "probed": probed,
       "cells_empty": sum(1 for c in cells if c["total"] == 0),
       "cells_no_alive": sum(1 for c in cells if c["alive"] == 0),
       "weakest": cells[:3]}
with open(LEDGER, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
