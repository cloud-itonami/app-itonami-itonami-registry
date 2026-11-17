#!/usr/bin/env python3
"""Build the Itonami Registry website and static JSON API (ADR 0002).

    python scripts/build_site.py [--out site]

The Hermes registry serves its catalog from a Next.js app over Postgres; this
registry is static: everything a client needs is a file, so it can be served
from GitHub Pages (or any static host) and verified against git.

    site/index.html                                   browse / search
    site/api/v1/index.json                            every entry, all registries
    site/api/v1/categories.json, models.json          Hermes registry shapes
    site/api/v1/registries.json                       which registries, which commits
    site/api/v1/api-classification.json               ADR 0005 classification of API repositories
    site/api/v1/entries/<registry>/<type>/<id>.json   one entry with its manifest

Entries keep registry-qualified identities (`itonami-registry/profile/itonami-eng`,
`hermes-registry/agent/architect`), so the two catalogs never collide.
"""
import argparse
import json
import shutil
from pathlib import Path

from build_index import ROOT, frontmatter

REGISTRY = {'id': 'itonami-registry', 'repository': 'cloud-itonami/app-itonami-itonami-registry'}


def read(path):
    return json.loads(path.read_text())


def local_entries(root):
    index = read(root / 'index.json')
    for e in index['entries']:
        folder = root / e['path']
        if e['type'] == 'skill':
            detail = {'skill': frontmatter(folder / 'SKILL.md')}
        else:
            detail = {'manifest': read(folder / 'manifest.json')}
        if (folder / 'itonami.json').exists():
            detail['itonami'] = read(folder / 'itonami.json')
        row = dict(e, registry=REGISTRY['id'], qualifiedId=f"{REGISTRY['id']}/{e['type']}/{e['id']}",
                   folder=f"https://github.com/{REGISTRY['repository']}/tree/main/{e['path']}")
        yield row, detail


def federated_entries(root):
    for path in sorted((root / 'catalogs/federated').glob('*.json')):
        snap = read(path)
        reg = snap['registry']
        for e in snap['entries']:
            row = dict(e, registry=reg['id'],
                       folder=f"https://github.com/{reg['repository']}/tree/{reg['commit']}/{e['path']}")
            yield row, {'resolve': {'repository': reg['repository'], 'commit': reg['commit'],
                                    'path': e['path'], 'checksum': e['checksum']}}


def install_hint(row, detail):
    """How to use the entry, by type — shown on the site, never executed."""
    t = row['type']
    if t == 'profile':
        prof = detail['manifest']['profile']
        return {'itonami': 'Cloud Itonami → Marketplace → Bots: add it (installs inert; you bind accounts).',
                'hermes': (f"git clone https://github.com/{prof['repository']} && "
                           f"git -C {prof['repository'].split('/')[1]} checkout {prof['commit']} && "
                           f"cp -R {prof['repository'].split('/')[1]}/{prof['path']} ~/.hermes/profiles/{row['id']}")}
    if t == 'skill':
        return {'hermes': f"Copy {row['path']}/SKILL.md into ~/.hermes/skills/{row.get('category', 'misc')}/{row['id']}/"}
    if t == 'agent':
        return {'itonami': 'Cloud Itonami → Marketplace → Bots (inert install).'}
    if t == 'api':
        pin = detail['manifest']['pin']
        return {'itonami': (f"Shape reference only; nothing to install or run. Read manifest.json at "
                            f"https://github.com/{pin['repository']}/blob/{pin['commit']}/{pin.get('path', '').rstrip('/') + '/' if pin.get('path') else ''}manifest.json and "
                            f"verify its sha256 against this entry.")}
    return {}


def build(root, out):
    if out.exists():
        shutil.rmtree(out)
    api = out / 'api/v1'
    rows = []
    for row, detail in list(local_entries(root)) + list(federated_entries(root)):
        row = dict(row, install=install_hint(row, detail))
        rows.append(row)
        target = api / 'entries' / row['registry'] / row['type'] / f"{row['id']}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({'entry': row, **detail}, ensure_ascii=False, indent=2) + '\n')
    rows.sort(key=lambda r: (r['registry'] != REGISTRY['id'], r['type'], r['id']))
    generated = read(root / 'index.json')['generated']
    registries = [dict(REGISTRY, commit='main', count=sum(r['registry'] == REGISTRY['id'] for r in rows))]
    for path in sorted((root / 'catalogs/federated').glob('*.json')):
        snap = read(path)
        registries.append(dict(snap['registry'], count=snap['count']))
    (api / 'index.json').write_text(json.dumps(
        {'schemaVersion': '1', 'generated': generated, 'count': len(rows), 'registries': registries,
         'entries': [{k: v for k, v in r.items() if k != 'install'} for r in rows]},
        ensure_ascii=False, indent=2) + '\n')
    (api / 'registries.json').write_text(json.dumps({'registries': registries}, ensure_ascii=False, indent=2) + '\n')
    for name in ['categories.json', 'models.json']:
        shutil.copy(root / name, api / name)
    shutil.copy(root / 'catalogs/api-classification.json', api / 'api-classification.json')
    shutil.copy(root / 'web/index.html', out / 'index.html')
    (out / '.nojekyll').write_text('')
    return len(rows)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', default=str(ROOT / 'site'))
    a = p.parse_args()
    print(f'built site with {build(ROOT, Path(a.out))} entries')
