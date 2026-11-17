#!/usr/bin/env python3
"""hiraku-soudan: look up grounded resources for a consultation.

  python3 hiraku_lookup.py [--axis gender,region] [--stage junior_high] [--lang pt] [--kind learning]
  python3 hiraku_lookup.py --safety

Prints only what is in data/catalog.json / data/safety.json. The agent answers
from these lines and nothing else when naming a service, phone number or URL.
Read-only; stores nothing about the person asking.
"""
import argparse, json, os, sys

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


def load(name):
    with open(os.path.join(REPO, "data", name), encoding="utf-8") as f:
        return json.load(f)


ap = argparse.ArgumentParser()
ap.add_argument("--axis", default="")
ap.add_argument("--stage", default="")
ap.add_argument("--lang", default="")
ap.add_argument("--kind", default="")
ap.add_argument("--safety", action="store_true")
ap.add_argument("--limit", type=int, default=8)
a = ap.parse_args()

if a.safety:
    for x in load("safety.json")["emergency"]:
        print("SAFETY\t%s\t%s\t%s\t%s" % (x["name"], x["phone"], x.get("hours", "-"), x.get("for", "-")))
    sys.exit(0)

axes = [x for x in a.axis.split(",") if x]
rows = []
for e in load("catalog.json")["entries"]:
    if a.stage and a.stage not in e["stages"]:
        continue
    if a.kind and e["kind"] != a.kind:
        continue
    score = sum(1 for x in axes if x in e["axes"])
    if axes and score == 0:
        continue
    if a.lang and a.lang not in e.get("langs", []):
        score -= 1  # still shown, but after entries in the asked language
    rows.append((-score, e.get("cost") != "free", e["id"], e))

rows.sort(key=lambda r: r[:3])
for *_, e in rows[: a.limit]:
    print("RESOURCE\t%s\t%s\t%s\t%s\t%s\tlangs=%s\t%s" % (
        e["id"], e["name"], e.get("url", "-"), e.get("phone", "-"), e.get("cost", "-"),
        ",".join(e.get("langs", [])), e.get("easy_ja", "")))
if not rows:
    print("RESOURCE\tnone\tカタログに該当なし — 作らずに「まだ見つけられていない」と伝え、--safety の総合窓口を案内する")
