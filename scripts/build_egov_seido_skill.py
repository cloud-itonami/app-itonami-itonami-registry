#!/usr/bin/env python3
"""Build skills/knowledge/egov-seido-packs from network-awai/app-itonami-egov (ADR 0019, AWAI-3421).

    python scripts/build_egov_seido_skill.py --checkout ~/github/network-awai/app-itonami-egov --commit <sha>

Reads seido/*.edn from git objects at the commit (never the working tree), copies them verbatim to
references/seido/, writes references/index.json, SKILL.md and itonami.json, records the file hashes as one
source in catalogs/sources.json and the registration in catalogs/targeted-public-sources.json.
Nothing is executed and no pack is interpreted beyond reading a few top-level keys for the index.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / 'skills/knowledge/egov-seido-packs'
REPO = 'network-awai/app-itonami-egov'
ENTRY = 'skill/egov-seido-packs'


def git(checkout, *args):
    return subprocess.run(['git', '-C', str(checkout), *args], check=True, capture_output=True).stdout


def kw(text, key):
    m = re.search(r':' + re.escape(key) + r'\s+("(?:[^"\\]|\\.)*"|:[\w.\-/]+|\[[^\]]*\]|true|false|nil)', text)
    if not m:
        return None
    v = m.group(1)
    return v[1:-1] if v.startswith('"') else v


def subdivisions(text):
    """Subdivision keys and whether each is a fixture, read from the :pack/subdivisions map."""
    out = []
    for m in re.finditer(r'(:[\w.\-]+/[\w.\-]+)\s*\{:name\s+"((?:[^"\\]|\\.)*)"[^{}]*?:fixture\s+(true|false)', text):
        out.append({'key': m.group(1), 'name': m.group(2), 'fixture': m.group(3) == 'true'})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkout', required=True)
    ap.add_argument('--commit', required=True)
    a = ap.parse_args()
    commit = git(a.checkout, 'rev-parse', a.commit + '^{commit}').decode().strip()
    names = [p for p in git(a.checkout, 'ls-tree', '--name-only', commit, 'seido/').decode().split() if p.endswith('.edn')]
    if not names:
        raise SystemExit('no seido/*.edn at commit')
    files, index = [], []
    for path in sorted(names):
        b = git(a.checkout, 'show', f'{commit}:{path}')
        text = b.decode('utf-8')
        out = SK / 'references' / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b)
        sha = hashlib.sha256(b).hexdigest()
        files.append({'path': path, 'sha256': sha, 'url': f'https://github.com/{REPO}/blob/{commit}/{path}'})
        index.append({
            'file': f'references/{path}', 'sha256': sha,
            'pack-id': kw(text, 'pack/id'), 'version': kw(text, 'pack/version'),
            'jurisdiction': kw(text, 'pack/jurisdiction'), 'language': kw(text, 'pack/language'),
            'checked-on': kw(text, 'pack/checked-on'), 'review-by': kw(text, 'pack/review-by'),
            'review-status': kw(text, 'review/status'),
            'procedures': re.findall(r':procedure/id\s+(:[\w.\-/]+)', text),
            'subdivisions': subdivisions(text)})
    (SK / 'references/index.json').write_text(json.dumps({'count': len(index), 'source': {'repository': REPO, 'commit': commit},
                                                          'packs': index}, ensure_ascii=False, indent=1) + '\n')
    tree = f'https://github.com/{REPO}/tree/{commit}'
    (SK / 'SKILL.md').write_text(f'''---
name: egov-seido-packs
description: Read the Itonami institution packs (seido) that say which government procedures may apply to an address change, with their primary legal sources, deadlines and review state. Use with the Shakai, Kaisha and Matsuri e-government profiles, or when a user in a covered country asks what to file after moving.
license: AGPL-3.0-or-later
metadata:
  hermes:
    version: 0.1.0
    author: network-awai
    source: {tree}
    compatibility:
      hermes: '*'
      desktop: '*'
---

# E-government institution packs

`references/seido/*.edn` are verbatim copies of the institution packs in `{REPO}` at `{commit[:8]}`. Each pack holds, for
one country: procedures (who, when it applies, deadline, where to submit), the primary legal sources with retrieval
date and sha256, subdivisions (real municipalities are marked `:fixture false`; test ones `:fixture true`) and local
reference documents. `references/index.json` lists the packs, their review state and procedures.

The packs are evaluated by the pure functions in `src/itonami/egov/core.cljc` of the same repository (the Gyosei screen
in the Itonami app and the egov profiles use them). This skill carries the data so an assistant can read it.

## How to answer

1. Find the country in `references/index.json`. If there is no pack, say the procedures are not covered; do not answer
   from memory. A pack that needs a subdivision (for example the United States without a state) gives no candidates.
2. If today is after `review-by`, say the pack is out of date and stop; do not give candidates from it.
3. Give the procedures as candidates, each with its source title, issuer, retrieval date and URL. Say that the
   authority decides whether the filing is required or accepted. While `review-status` is `:unreviewed`, do not
   propose submitting anything.
4. Local references of a municipality are rules to read, not procedures. For municipalities without a pack entry, use
   `skill/municipal-ordinance-knowledge`.

## Limits

- No expert review yet. Only what each pack lists is covered.
- Do not collect personal data. Nothing here files, signs, pays or sends on the user's behalf.
''')
    (SK / 'itonami.json').write_text(json.dumps({
        'schemaVersion': 'itonami.entry.v1',
        'sourceRefs': [f'app-itonami-egov-seido-{commit[:8]}'],
        'useWhen': 'A user asks which government procedures follow an address change in a country that has an institution pack, or an egov profile (Shakai, Kaisha, Matsuri) needs the pack data.',
        'avoidWhen': 'The country has no pack, the pack is past its review date, or the user wants a determination, legal advice or a filing made for them.',
        'inputs': {'jurisdiction': 'country, and subdivision where the pack requires one'},
        'outputs': {'answer': 'candidate procedures with primary sources, deadlines, submission target and review state'},
        'effects': ['filesystem-read'],
        'authority': {'grants': False, 'default': 'blocked', 'binding': 'caller authorization; read-only reference material'},
        'validation': {'catalog': 'schema-checked',
                       'runtime': f'{len(index)} pack files copied verbatim from the pinned commit; evaluated by the source repository tests (bb test), not by an agent through this skill',
                       'live': False},
        'compatibilityNote': 'Hermes skill shape with bundled references. Wildcard versions express no runtime compatibility.',
    }, ensure_ascii=False, indent=2) + '\n')
    sid = f'app-itonami-egov-seido-{commit[:8]}'
    sp = ROOT / 'catalogs/sources.json'
    src = json.loads(sp.read_text())
    src['sources'] = [s for s in src['sources'] if not s['id'].startswith('app-itonami-egov-seido-')]
    src['sources'].append({'id': sid, 'repository': REPO, 'commit': commit, 'files': files})
    sp.write_text(json.dumps(src, ensure_ascii=False, indent=2) + '\n')
    tp = ROOT / 'catalogs/targeted-public-sources.json'
    tps = json.loads(tp.read_text())
    row = next((r for r in tps['sources'] if r['repository'] == REPO), None)
    if row is None:
        raise SystemExit(f'not in targeted-public-sources: {REPO}')
    row['registrations'] = [r for r in row['registrations'] if r['entry'] != ENTRY] + [{'entry': ENTRY, 'sourceCommit': commit}]
    row['registrations'].sort(key=lambda x: (x['entry'], x['sourceCommit']))
    tp.write_text(json.dumps(tps, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(index)} packs from {REPO}@{commit[:8]}')


if __name__ == '__main__':
    main()
