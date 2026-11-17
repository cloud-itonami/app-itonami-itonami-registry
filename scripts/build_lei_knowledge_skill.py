#!/usr/bin/env python3
"""Build skills/knowledge/corporate-entity-knowledge from catalogs/datasets/lei.json (ADR 0017).

Downloads each listed file at its pinned commit over raw.githubusercontent.com, checks the sha256 recorded in the
dataset catalog, writes it under references/lei/<lei>/, builds references/index.json for lookup by name, and records
provenance in catalogs/sources.json and catalogs/inventory.json. Nothing is executed.
"""
import concurrent.futures as cf, hashlib, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / 'skills/knowledge/corporate-entity-knowledge'
ENTRY = 'skill/corporate-entity-knowledge'


def raw(repo, commit, path):
    url = f'https://raw.githubusercontent.com/{repo}/{commit}/{path}'
    for t in range(5):
        try:
            return urllib.request.urlopen(url, timeout=60).read()
        except Exception:
            time.sleep(1 + t)
    raise SystemExit(f'fetch failed: {url}')


def field(text, key):
    m = re.search(r':company/' + key + r'\s+"((?:[^"\\]|\\.)*)"', text)
    return m.group(1) if m else None


def main():
    entries = json.loads((ROOT / 'catalogs/datasets/lei.json').read_text())['entries']
    jobs = [(e, p) for e in entries for p in e['payload']]

    def get(j):
        e, p = j
        b = raw(e['repository'], e['commit'], p['path'])
        if hashlib.sha256(b).hexdigest() != p['sha256']:
            raise SystemExit(f"digest mismatch: {e['id']}/{p['path']}")
        return e['id'], p['path'], b

    with cf.ThreadPoolExecutor(8) as ex:
        got = list(ex.map(get, jobs))
    index, sources_new = [], []
    data = {}
    for eid, path, b in got:
        data.setdefault(eid, {})[path] = b
    for e in entries:
        lei = e['keys']['lei']
        folder = SK / 'references/lei' / lei.lower()
        for p in e['payload']:
            out = folder / p['path'].split('/')[-1]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data[e['id']][p['path']])
        bp = data[e['id']].get('blueprint.edn', b'').decode('utf-8', 'replace')
        index.append({'lei': lei, 'name': field(bp, 'legal-name'), 'jurisdiction': e['keys'].get('jurisdiction') or field(bp, 'jurisdiction'),
                      'website': field(bp, 'website'), 'ticker': field(bp, 'ticker'),
                      'files': sorted(p['path'].split('/')[-1] for p in e['payload']), 'dir': f'references/lei/{lei.lower()}'})
        sources_new.append({'id': f"lei-{lei.lower()}-{e['commit'][:8]}", 'repository': e['repository'], 'commit': e['commit'],
                            'files': sorted(({'path': p['path'], 'sha256': p['sha256'],
                                              'url': f"https://github.com/{e['repository']}/blob/{e['commit']}/{p['path']}"} for p in e['payload']),
                                            key=lambda f: f['path'])})
    index.sort(key=lambda r: r['lei'])
    (SK / 'references').mkdir(parents=True, exist_ok=True)
    (SK / 'references/index.json').write_text(json.dumps({'count': len(index), 'entities': index}, ensure_ascii=False, indent=1) + '\n')
    first = sources_new[0]
    (SK / 'SKILL.md').write_text(f'''---
name: corporate-entity-knowledge
description: Look up what the Itonami archive knows about a company by its LEI or name, covering verified public-registry facts, the company profile and the text of its published Terms of Use. Use when a user asks about one of these companies or their terms.
license: AGPL-3.0-or-later
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: https://github.com/{first['repository']}/tree/{first['commit']}
    compatibility:
      hermes: '*'
      desktop: '*'
---

# Corporate entity knowledge

This skill carries the Itonami archive of {len(index)} legal entities, keyed by LEI (ISO 17442). The facts come from public
registries and the companies' own sites; each entity folder is a verbatim copy of an independent archive and is **not
affiliated with the company**. It is reference material, not legal advice.

## How to answer a question about a company

1. Open `references/index.json`. Find the entity by `lei` (exact) or by `name` (case-insensitive substring; confirm with
   the user if several match). Each row has `jurisdiction`, `website`, `ticker` and the `dir` of its folder.
2. Read only what the question needs from `references/lei/<lei>/` (lower-case LEI):
   - `blueprint.edn`: short profile (legal name, address, phone, website, ticker, retrieval note). Start here.
   - `facts.edn`: verified registry facts (legal form, status, parent/ultimate-parent or the reporting exception),
     each with its source URL and retrieval time. Use it for ownership and status questions.
   - `tos.journal.edn`: the full text of the company's published Terms of Use as tx-data. It is long; search it for the
     clause in question instead of reading it whole, and quote sparingly.
3. State where the answer comes from (file and the `:source/retrieved-at` or retrieval date). These files are snapshots
   from 2026; say so, and do not claim they are current. For anything that matters, tell the user to check the company's
   own current page.
4. If the entity is not in the index, say the archive does not cover it. Do not guess from memory.

## Limits

- Terms of Use text is the company's copyright; use it to answer and cite, not to republish.
- Nothing here grants authority to act for or contact the company.
''')
    (SK / 'itonami.json').write_text(json.dumps({
        'schemaVersion': 'itonami.entry.v1',
        'sourceRefs': [s['id'] for s in sources_new],
        'useWhen': 'The user asks about a company covered by the archive (by LEI or name): its registry facts, ownership, profile or Terms of Use.',
        'avoidWhen': 'The company is not in references/index.json, or the user needs current information or legal advice.',
        'inputs': {'entity': 'LEI or company name'},
        'outputs': {'answer': 'facts and quotes from the archived files, with their source and retrieval date'},
        'effects': ['filesystem-read'],
        'authority': {'grants': False, 'default': 'blocked', 'binding': 'caller authorization; read-only reference material'},
        'validation': {'catalog': 'schema-checked', 'runtime': f'{len(index)} entity folders copied verbatim from pinned commits on 2026-11-17 and checked against the dataset catalog sha256; lookup procedure not run by an agent',
                       'live': False},
        'compatibilityNote': 'Hermes skill shape with bundled references (progressive disclosure through references/index.json). Wildcard versions express no runtime compatibility.',
    }, ensure_ascii=False, indent=2) + '\n')
    sp = ROOT / 'catalogs/sources.json'
    src = json.loads(sp.read_text())
    have = {s['id'] for s in src['sources']}
    src['sources'] += [s for s in sources_new if s['id'] not in have]
    sp.write_text(json.dumps(src, ensure_ascii=False, indent=2) + '\n')
    ip = ROOT / 'catalogs/inventory.json'
    inv = json.loads(ip.read_text())
    by = {r['repository']: r for r in inv['repositories']}
    for s in sources_new:
        row = by.get(s['repository'])
        if row is None:
            raise SystemExit(f"not in inventory: {s['repository']}")
        reg = {'sourceCommit': s['commit'], 'entry': ENTRY}
        if reg not in row['registrations']:
            row['registrations'].append(reg)
            row['registrations'].sort(key=lambda x: (x['entry'], x['sourceCommit']))
    ip.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(index)} entities, {len(got)} files')


if __name__ == '__main__':
    sys.exit(main())
