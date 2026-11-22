#!/usr/bin/env python3
"""Build skills/knowledge/municipal-ordinance-knowledge and workflows/municipal-procedure-guide from
catalogs/datasets/municipality.json (ADR 0018). Files are copied verbatim at their pinned commit and checked
against the dataset catalog sha256. Nothing is executed.

    python scripts/build_municipality_knowledge.py                # fetch the pinned commits
    python scripts/build_municipality_knowledge.py --from-copies  # rebuild from the copies already here
"""
import concurrent.futures as cf, hashlib, json, re, sys, time, urllib.request
from collections.abc import Mapping
from pathlib import Path

import edn_format

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / 'skills/knowledge/municipal-ordinance-knowledge'
WF = ROOT / 'workflows/municipal-procedure-guide'
SKILL_ENTRY = 'skill/municipal-ordinance-knowledge'
WF_ENTRY = 'workflow/municipal-procedure-guide'
SEIDO_ENTRY = 'skill/egov-seido-packs'  # ADR 0019: national procedures with primary legal sources


def raw(repo, commit, path):
    url = f'https://raw.githubusercontent.com/{repo}/{commit}/{path}'
    for t in range(5):
        try:
            return urllib.request.urlopen(url, timeout=60).read()
        except Exception:
            time.sleep(1 + t)
    raise SystemExit(f'fetch failed: {url}')


def kw(text, key):
    m = re.search(r':' + re.escape(key) + r'\s+"((?:[^"\\]|\\.)*)"', text)
    return m.group(1) if m else None


def ordinance_count(text):
    """How many ordinance records a datascript-tx.edn holds.

    The archives are EDN vectors of `#:ordinance{...}` maps whose keys are not in a fixed order:
    some start with `:id`, others with `:kind` or `:citation-control`. The records therefore have
    to be read as EDN; a text search for `#:ordinance{:id` reports 0 for every archive that sorts
    its keys differently (deu-munich and 15 others before this was fixed). A record is counted
    when it carries `:ordinance/id`.
    """
    forms = edn_format.loads(text)
    if isinstance(forms, Mapping):
        forms = [forms]
    return sum(1 for form in forms
               if isinstance(form, Mapping) and edn_format.Keyword('ordinance/id') in form)


def local_copies(entries):
    """The already-copied archives, checked against the dataset catalog sha256.

    The upstream municipality repositories are not all reachable any more (their archives were moved
    into this registry in AWAI-3088), so a rebuild has to be able to run from the copies that are
    already here. Each file is checked against catalogs/datasets/municipality.json before use.
    """
    data = {}
    for e in entries:
        mid = e['id'].split('/', 1)[1]
        folder = SK / 'references/municipality' / mid
        for p in e['payload']:
            b = (folder / p['path'].split('/')[-1]).read_bytes()
            if hashlib.sha256(b).hexdigest() != p['sha256']:
                raise SystemExit(f"digest mismatch in copy: {mid}/{p['path']}")
            data.setdefault(e['id'], {})[p['path']] = b
    return data


def main():
    entries = json.loads((ROOT / 'catalogs/datasets/municipality.json').read_text())['entries']
    jobs = [(e, p) for e in entries for p in e['payload']]

    def get(j):
        e, p = j
        b = raw(e['repository'], e['commit'], p['path'])
        if hashlib.sha256(b).hexdigest() != p['sha256']:
            raise SystemExit(f"digest mismatch: {e['id']}/{p['path']}")
        return e['id'], p['path'], b

    if '--from-copies' in sys.argv[1:]:
        data = local_copies(entries)
        got = [(eid, path, b) for eid, files in data.items() for path, b in files.items()]
    else:
        with cf.ThreadPoolExecutor(8) as ex:
            got = list(ex.map(get, jobs))
        data = {}
        for eid, path, b in got:
            data.setdefault(eid, {})[path] = b
    index, sources = [], []
    for e in entries:
        mid = e['id'].split('/', 1)[1]
        folder = SK / 'references/municipality' / mid
        for p in e['payload']:
            out = folder / p['path'].split('/')[-1]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data[e['id']][p['path']])
        org = data[e['id']].get('organization.edn', b'').decode('utf-8', 'replace')
        tx = data[e['id']].get('data/datascript-tx.edn', b'').decode('utf-8', 'replace')
        index.append({'id': mid, 'country': e['keys'].get('country'), 'name': e.get('name') or kw(org, 'name-en'), 'name-local': kw(org, 'name-local'),
                      'official-url': kw(org, 'official-url'), 'wikidata': kw(org, 'wikidata'),
                      'ordinances': ordinance_count(tx), 'dir': f'references/municipality/{mid}'})
        sources.append({'id': f"municipality-{mid}-{e['commit'][:8]}", 'repository': e['repository'], 'commit': e['commit'],
                        'files': sorted(({'path': p['path'], 'sha256': p['sha256'],
                                          'url': f"https://github.com/{e['repository']}/blob/{e['commit']}/{p['path']}"} for p in e['payload']),
                                        key=lambda f: f['path'])})
    index.sort(key=lambda r: (r['country'] or '', r['id']))
    (SK / 'references').mkdir(parents=True, exist_ok=True)
    (SK / 'references/index.json').write_text(json.dumps({'count': len(index), 'municipalities': index}, ensure_ascii=False, indent=1) + '\n')
    first = sources[0]
    tree = f"https://github.com/{first['repository']}/tree/{first['commit']}"
    (SK / 'SKILL.md').write_text(f'''---
name: municipal-ordinance-knowledge
description: Look up what the Itonami archive knows about a municipality, covering its official organization details and a catalog of its ordinances with official source links. Use when a user asks about local rules or an administrative procedure in one of these cities.
license: AGPL-3.0-or-later
metadata:
  hermes:
    version: 0.1.0
    author: cloud-itonami
    source: {tree}
    compatibility:
      hermes: '*'
      desktop: '*'
---

# Municipal ordinance knowledge

This skill carries the Itonami archive of {len(index)} municipalities. Each folder is a verbatim copy of an independent archive:
the municipality's official identity (`organization.edn`), an ordinance catalog with titles, enactment dates and official
URLs (`data/datascript-tx.edn`, copied as `datascript-tx.edn`) and the blueprint record (`blueprint.edn`). It is an **index of
rules and where to read them**, not a description of procedures, and not legal advice.

## How to answer

1. Open `references/index.json` and find the municipality by `id`, `name`, `name-local` or `country`. If several match,
   ask the user which one.
2. Read `references/municipality/<id>/organization.edn` for the official site and organization details, and
   `datascript-tx.edn` for the ordinance catalog (`:ordinance/title`, `:ordinance/url`, `:ordinance/enacted-date`,
   `:ordinance/retrieved-at`).
3. Point the user to the official source URL of the relevant ordinance and say when the catalog entry was retrieved
   (2026 snapshot). Do not paraphrase an ordinance from the catalog alone: the catalog does not contain its text.
4. If the municipality or topic is not covered, say so. Do not answer from memory.

For a step-by-step procedure, use the `workflow/municipal-procedure-guide` recipe.

## Limits

- Snapshot data; rules change. Tell the user to confirm on the official site.
- No personal data about office-holders is stored; do not ask for or infer any.
- Nothing here lets you file, apply or contact the municipality on the user's behalf.
''')
    (SK / 'itonami.json').write_text(json.dumps({
        'schemaVersion': 'itonami.entry.v1',
        'sourceRefs': [s['id'] for s in sources],
        'useWhen': 'The user asks about local rules or an administrative procedure in a covered municipality.',
        'avoidWhen': 'The municipality is not in references/index.json, or the user needs current rules, the text of an ordinance or legal advice.',
        'inputs': {'municipality': 'id, name or country'},
        'outputs': {'answer': 'organization details and ordinance catalog entries with official URLs and retrieval dates'},
        'effects': ['filesystem-read'],
        'authority': {'grants': False, 'default': 'blocked', 'binding': 'caller authorization; read-only reference material'},
        'validation': {'catalog': 'schema-checked', 'runtime': f'{len(index)} municipality folders copied verbatim from pinned commits on 2026-11-17 and checked against the dataset catalog sha256; lookup procedure not run by an agent', 'live': False},
        'compatibilityNote': 'Hermes skill shape with bundled references (progressive disclosure through references/index.json). Wildcard versions express no runtime compatibility.',
    }, ensure_ascii=False, indent=2) + '\n')
    WF.mkdir(parents=True, exist_ok=True)
    (WF / 'manifest.json').write_text(json.dumps({
        'schemaVersion': '1', 'type': 'workflow', 'id': 'municipal-procedure-guide', 'name': 'municipal-procedure-guide', 'version': '0.1.0',
        'description': 'Guide a user through finding the rules and official sources for an administrative procedure in a covered municipality, and hand off to the official channel. Never files or applies for the user.',
        'author': 'cloud-itonami', 'license': 'AGPL-3.0-or-later', 'source': tree,
        'compatibility': {'hermes': '*', 'desktop': '*'}, 'entry': 'workflow.json',
        'requires': [SKILL_ENTRY, SEIDO_ENTRY], 'permissions': ['filesystem:read']}, indent=2) + '\n')
    (WF / 'workflow.json').write_text(json.dumps({
        'schemaVersion': 'itonami.workflow.v1', 'mode': 'recipe',
        'inputs': ['municipality', 'procedure', 'userSituation'],
        'steps': [
            {'id': 'identify', 'action': 'Confirm the municipality and what the user wants to do (the procedure). Ask only for what is needed; do not collect personal data.'},
            {'id': 'lookup', 'action': 'Find the municipality in the knowledge skill and list the ordinances that may apply, with their official URLs and retrieval dates. If the country has an institution pack, also list its candidate procedures with their primary sources and say whether the pack is current.', 'uses': [SKILL_ENTRY, SEIDO_ENTRY]},
            {'id': 'read-primary', 'action': 'Ask the user to open the official source, or, only if the user approves that exact request, fetch the official page; read the primary text before stating any rule.'},
            {'id': 'checklist', 'action': 'Produce a checklist of what the user must confirm or prepare, each item tied to its source; mark anything not found in the primary text as unknown.'},
            {'id': 'handoff', 'action': 'Point to the official channel for the procedure (site, office, contact from the organization record). State that the information is a snapshot and that the user files or applies personally.'}],
        'stopWhen': ['municipality-not-in-archive', 'request-needs-personal-data', 'user-asks-to-file-or-apply-on-their-behalf'],
        'automaticExecution': False}, indent=2) + '\n')
    (WF / 'itonami.json').write_text(json.dumps({
        'schemaVersion': 'itonami.entry.v1', 'sourceRefs': [first['id']],
        'useWhen': 'A user wants to know which local rules apply to something they want to do in a covered municipality and where to read them.',
        'avoidWhen': 'The municipality is not covered, the user wants the procedure carried out for them, or the question needs legal advice.',
        'inputs': {'parameters': ['municipality', 'procedure', 'userSituation']},
        'outputs': {'result': 'a sourced checklist and a hand-off to the official channel'},
        'effects': ['filesystem-read', 'user-approved-network-fetch'],
        'authority': {'grants': False, 'default': 'blocked', 'binding': 'the user approves each network fetch; the workflow never files or applies'},
        'validation': {'catalog': 'schema-checked', 'runtime': 'not-tested', 'live': False},
        'compatibilityNote': 'Hermes storage format only; client installation and execution are not qualified. Wildcard versions do not establish runtime compatibility.',
        'executionNote': 'workflow.json is an Itonami declarative recipe; no Hermes workflow executor compatibility is claimed.'}, indent=2) + '\n')
    sp = ROOT / 'catalogs/sources.json'
    src = json.loads(sp.read_text())
    have = {s['id'] for s in src['sources']}
    src['sources'] += [s for s in sources if s['id'] not in have]
    sp.write_text(json.dumps(src, ensure_ascii=False, indent=2) + '\n')
    ip = ROOT / 'catalogs/inventory.json'
    inv = json.loads(ip.read_text())
    by = {r['repository']: r for r in inv['repositories']}
    for i, s in enumerate(sources):
        row = by.get(s['repository'])
        if row is None:
            raise SystemExit(f"not in inventory: {s['repository']}")
        for entry in [SKILL_ENTRY] + ([WF_ENTRY] if i == 0 else []):
            reg = {'sourceCommit': s['commit'], 'entry': entry}
            if reg not in row['registrations']:
                row['registrations'].append(reg)
        row['registrations'].sort(key=lambda x: (x['entry'], x['sourceCommit']))
    ip.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(index)} municipalities, {len(got)} files')


if __name__ == '__main__':
    sys.exit(main())
