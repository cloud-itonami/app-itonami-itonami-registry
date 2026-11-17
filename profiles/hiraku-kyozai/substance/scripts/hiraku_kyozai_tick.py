#!/usr/bin/env python3
"""hiraku-kyozai: gate pending drafts, then say which material to write next.

1. Every workspace/kyozai/drafts/*.md is checked by the quality gate below.
   pass -> workspace/kyozai/ready/, fail -> workspace/kyozai/rejected/ (+ .reason).
2. The next (theme, stage, lang) cell with no ready material is printed as a
   BRIEF block the agent writes from, with the catalog entries it may cite.

The gate is the final word: the agent does not re-judge a draft it wrote.
Writes only inside the profile workspace. Emits MEASURE / GATE / BRIEF lines.
"""
import glob, json, os, re, shutil, sys, time

PROFILE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.join(PROFILE, "workspace")
KZ = os.path.join(WS, "kyozai")
DIRS = {k: os.path.join(KZ, k) for k in ("drafts", "ready", "rejected")}
LEDGER = os.path.join(WS, "kyozai-ledger.jsonl")
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
MAX_REJECTS_PER_CELL = 3

for d in DIRS.values():
    os.makedirs(d, exist_ok=True)


def m(k, v):
    print("MEASURE\t%s\t%s" % (k, v))


def load(name):
    with open(os.path.join(REPO, "data", name), encoding="utf-8") as f:
        return json.load(f)


try:
    axes, catalog, curriculum, safety = (load(n) for n in
                                         ("axes.json", "catalog.json", "curriculum.json", "safety.json"))
except Exception as e:
    m("data", "UNMEASURED %s" % type(e).__name__)
    sys.exit(1)

entries = {e["id"]: e for e in catalog["entries"]}
known_phones = {re.sub(r"[^0-9#]", "", x.get("phone", "")) for x in list(entries.values()) + safety["emergency"]}
known_phones.discard("")
known_hosts = set()
for x in list(entries.values()) + safety["emergency"]:
    if x.get("url"):
        known_hosts.add(re.sub(r"^https?://([^/]+).*$", r"\1", x["url"]).lower())

FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)


def front_matter(text):
    mt = FRONT.match(text)
    if not mt:
        return {}
    out = {}
    for line in mt.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def gate(text):
    """Return list of failure reasons (empty = pass)."""
    fails = []
    fm = front_matter(text)
    for k in ("theme", "stage", "lang", "title"):
        if not fm.get(k):
            fails.append("front-matter-missing:%s" % k)
    body = FRONT.sub("", text, count=1)
    n = len(body)
    if n < 400:
        fails.append("too-short:%d" % n)
    if n > 8000:
        fails.append("too-long:%d" % n)
    for marker in ("<!-- section:manabu -->", "<!-- section:ippo -->", "<!-- section:soudan -->"):
        if marker not in body:
            fails.append("section-missing:%s" % marker[13:-4])
    low = body.lower()
    for p in safety["banned_phrases"]:
        if p in body:
            fails.append("stereotype:%s" % p)
    for p in safety["banned_engagement_tokens"]:
        if p.lower() in low:
            fails.append("engagement:%s" % p)
    # nothing fabricated: every phone number and every link host must be known
    for ph in re.findall(r"(?<![0-9])(?:0\d{1,4}-\d{1,4}-\d{3,4}|#\d{4}|189|110|119)(?![0-9])", body):
        if re.sub(r"[^0-9#]", "", ph) not in known_phones:
            fails.append("unknown-phone:%s" % ph)
    for host in re.findall(r"https?://([^/\s)>\]]+)", body):
        if host.lower() not in known_hosts:
            fails.append("unknown-host:%s" % host)
    if not re.search(r"https?://|0120-|#8|189", body.split("<!-- section:soudan -->")[-1]):
        fails.append("soudan-without-contact")
    # やさしい日本語: short sentences
    if fm.get("lang") in ("ja-easy",) or fm.get("stage") == "elementary":
        sents = [s for s in re.split(r"[。！？\n]", re.sub(r"<!--.*?-->|https?://\S+|[#>*`|\-]", "", body)) if len(s.strip()) > 3]
        if sents:
            avg = sum(len(s) for s in sents) / len(sents)
            longest = max(len(s) for s in sents)
            if avg > 35:
                fails.append("easy-avg-sentence:%.0f" % avg)
            if longest > 80:
                fails.append("easy-long-sentence:%d" % longest)
    return fails, fm


def cell_key(fm):
    return "%s|%s|%s" % (fm.get("theme"), fm.get("stage"), fm.get("lang"))


# --- 1. gate drafts ---
passed = failed = 0
for path in sorted(glob.glob(os.path.join(DIRS["drafts"], "*.md"))):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fails, fm = gate(text)
    name = os.path.basename(path)
    if fails:
        failed += 1
        shutil.move(path, os.path.join(DIRS["rejected"], name))
        with open(os.path.join(DIRS["rejected"], name + ".reason"), "w", encoding="utf-8") as f:
            f.write("\n".join(fails) + "\n")
        print("GATE\tfail\t%s\t%s" % (name, ";".join(fails)))
    else:
        passed += 1
        shutil.move(path, os.path.join(DIRS["ready"], name))
        print("GATE\tpass\t%s\t%s" % (name, cell_key(fm)))


def cells_in(dirname):
    seen = {}
    for p in glob.glob(os.path.join(DIRS[dirname], "*.md")):
        with open(p, encoding="utf-8") as f:
            k = cell_key(front_matter(f.read()))
        seen[k] = seen.get(k, 0) + 1
    return seen


ready = cells_in("ready")
rejected = cells_in("rejected")

# --- 2. next cell: themes in order, then stage, then language rotation ---
all_cells = [(t, s, l) for l in curriculum["langs_rotation"] for t in curriculum["themes"] for s in t["stages"]]
nxt = None
for t, s, l in all_cells:
    k = "%s|%s|%s" % (t["id"], s, l)
    if k not in ready and rejected.get(k, 0) < MAX_REJECTS_PER_CELL:
        nxt = (t, s, l)
        break

m("drafts-gated", passed + failed)
m("gate-pass", passed)
m("gate-fail", failed)
m("ready-total", sum(ready.values()))
m("cells-ready", "%d/%d" % (len(ready), len(all_cells)))
m("cells-stuck", ",".join(k for k, v in rejected.items() if v >= MAX_REJECTS_PER_CELL and k not in ready) or "none")

with open(LEDGER, "a", encoding="utf-8") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gate_pass": passed, "gate_fail": failed,
                        "ready_total": sum(ready.values()), "cells_ready": len(ready),
                        "cells_total": len(all_cells),
                        "next": None if not nxt else "%s|%s|%s" % (nxt[0]["id"], nxt[1], nxt[2])},
                       ensure_ascii=False) + "\n")

if not nxt:
    print("BRIEF\tnone\tall cells have ready material or are stuck")
    sys.exit(0)

t, s, l = nxt
stage_ja = {x["id"]: x["ja"] for x in axes["stages"]}[s]
fname = "%s__%s__%s__%s.md" % (time.strftime("%Y%m%d-%H%M"), t["id"], s, l)
print("BRIEF\ttheme\t%s" % t["id"])
print("BRIEF\ttitle\t%s" % t["title"])
print("BRIEF\tgoal\t%s" % t["goal"])
print("BRIEF\tstage\t%s（%s）" % (s, stage_ja))
print("BRIEF\tlang\t%s" % l)
print("BRIEF\taxes\t%s" % ",".join(t["axes"]))
print("BRIEF\toutput\t%s" % os.path.join(DIRS["drafts"], fname))
for lid in t["links"]:
    e = entries.get(lid)
    if e:
        print("CITE\t%s\t%s\t%s\t%s" % (e["name"], e.get("url", "-"), e.get("phone", "-"), e.get("easy_ja", "")))
for x in safety["emergency"]:
    if x["id"] in ("childline", "kodomo-sos", "yorisoi", "jidosodan-189"):
        print("SAFETY\t%s\t%s\t%s" % (x["name"], x["phone"], x.get("url", "-")))
prev = rejected.get("%s|%s|%s" % (t["id"], s, l), 0)
if prev:
    reasons = []
    for p in glob.glob(os.path.join(DIRS["rejected"], "*__%s__%s__%s.md.reason" % (t["id"], s, l))):
        with open(p, encoding="utf-8") as f:
            reasons.append(f.read().strip().replace("\n", ";"))
    print("BRIEF\tprevious-rejects\t%d\t%s" % (prev, " | ".join(reasons)))
