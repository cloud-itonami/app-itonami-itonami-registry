#!/usr/bin/env python3
"""Build catalogs/datasets/<family>.json (ADR 0004).

Reads the public repository list and default-branch commits from GitHub (read-only
GraphQL), then hashes payload files from the pinned commit in a local clone when
that commit object is present. Copies no repository content and executes nothing
from the repositories. Without a local object the entry is `unverified`.

    build_dataset_catalog.py --clones DIR [--org cloud-itonami] [--observed-on YYYY-MM-DD]
                             [--out catalogs/datasets] [--check]
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 'itonami.dataset-sources.v1'
METHOD = ('GitHub GraphQL default-branch commit + license; payload sha256 read from the pinned commit in a '
          'local clone when its object is present, else unverified. Repository content is not copied.')

FAMILIES = {
    'lei': {
        'prefix': 'cloud-itonami-lei-',
        'repo': re.compile(r'^cloud-itonami-lei-([a-z0-9]{20})$'),
        'payload': ['blueprint.edn', 'facts.edn', '80-data/public/tos.journal.edn'],
    },
    'assoc': {
        'prefix': 'cloud-itonami-assoc-',
        'repo': re.compile(r'^cloud-itonami-assoc-([0-9]{4}-[a-z]{2,3}-[a-z0-9-]+)$'),
        'payload': ['blueprint.edn', 'organization.edn', 'data/datascript-tx.edn'],
    },
    'municipality': {
        'prefix': 'cloud-itonami-municipality-',
        'repo': re.compile(r'^cloud-itonami-municipality-([a-z]{2,3}-[a-z0-9-]+)$'),
        'payload': ['blueprint.edn', 'organization.edn', 'data/datascript-tx.edn'],
    },
}


def edn_string(text, key):
    """First `key "value"` in an EDN map; the sources are flat maps, so no parser is needed."""
    m = re.search(re.escape(key) + r'\s+"((?:[^"\\]|\\.)*)"', text)
    return m.group(1).replace('\\"', '"') if m else None


def gh_json(args):
    return json.loads(subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout)


def remote_state(org, names):
    """{name: (commit, spdx, archived)} for public repositories, via batched read-only GraphQL."""
    out = {}
    for i in range(0, len(names), 40):
        chunk = names[i:i + 40]
        body = ' '.join(
            f'r{j}: repository(owner: "{org}", name: "{n}") {{ name isArchived isPrivate '
            f'licenseInfo {{ spdxId }} defaultBranchRef {{ target {{ oid }} }} }}'
            for j, n in enumerate(chunk))
        data = gh_json(['api', 'graphql', '-f', f'query=query {{ {body} }}'])['data']
        for r in data.values():
            if r and not r['isPrivate'] and r['defaultBranchRef']:
                out[r['name']] = (r['defaultBranchRef']['target']['oid'],
                                  (r['licenseInfo'] or {}).get('spdxId') or 'NOASSERTION', r['isArchived'])
    return out


def git(clone, *args):
    return subprocess.run(['git', '-C', str(clone), *args], capture_output=True)


def blob(clone, commit, path):
    r = git(clone, 'show', f'{commit}:{path}')
    return r.stdout if r.returncode == 0 else None


def has_commit(clone, commit):
    return clone.is_dir() and git(clone, 'cat-file', '-e', f'{commit}^{{commit}}').returncode == 0


def make_entry(family, name, remote, clones):
    spec = FAMILIES[family]
    key = spec['repo'].match(name).group(1)
    commit, spdx, archived = remote
    clone = clones / name
    entry = {'id': f'{family}/{key}', 'repository': f'cloud-itonami/{name}', 'commit': commit,
             'visibility': 'public', 'archived': archived, 'license': spdx,
             'keys': {}, 'payload': [], 'digestStatus': 'unverified', 'status': 'repository-owned'}
    local = has_commit(clone, commit)
    texts = {}
    if local:
        for path in spec['payload']:
            data = blob(clone, commit, path)
            if data is not None:
                entry['payload'].append({'path': path, 'sha256': hashlib.sha256(data).hexdigest()})
                texts[path] = data.decode('utf-8', 'replace')
        if entry['payload']:
            entry['digestStatus'] = 'verified'
    if family == 'lei':
        entry['keys']['lei'] = key.upper()
        bp = texts.get('blueprint.edn', '')
        if edn_string(bp, ':company/legal-name'):
            entry['name'] = edn_string(bp, ':company/legal-name')
        if edn_string(bp, ':company/jurisdiction'):
            entry['keys']['jurisdiction'] = edn_string(bp, ':company/jurisdiction')
    else:
        org = texts.get('organization.edn', '')
        if edn_string(org, ':name-en'):
            entry['name'] = edn_string(org, ':name-en')
        for k, src in (('isic', ':isic'), ('country', ':country')):
            if edn_string(org, src):
                entry['keys'][k] = edn_string(org, src)
    entry['payload'].sort(key=lambda p: p['path'])
    return entry


def build(clones, org, observed_on):
    listing = gh_json(['repo', 'list', org, '--limit', '10000', '--json', 'name'])
    names = sorted(r['name'] for r in listing)
    remote = remote_state(org, [n for n in names if any(n.startswith(s['prefix']) for s in FAMILIES.values())])
    result, skipped = {}, []
    for family, spec in FAMILIES.items():
        rows = []
        for n in names:
            if not n.startswith(spec['prefix']):
                continue
            if not spec['repo'].match(n) or n not in remote:
                skipped.append(n)
                continue
            rows.append(make_entry(family, n, remote[n], clones))
        rows.sort(key=lambda e: e['id'])
        result[family] = {'schemaVersion': SCHEMA_VERSION, 'family': family, 'observedOn': observed_on,
                          'method': METHOD, 'count': len(rows), 'entries': rows}
    return result, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description='Build catalogs/datasets/<family>.json (ADR 0004)')
    ap.add_argument('--clones', type=Path, required=True, help='directory holding local clones named by repository')
    ap.add_argument('--org', default='cloud-itonami')
    ap.add_argument('--observed-on', default=date.today().isoformat())
    ap.add_argument('--out', type=Path, default=ROOT / 'catalogs/datasets')
    ap.add_argument('--check', action='store_true', help='fail if the files on disk differ from a fresh build')
    a = ap.parse_args(argv)
    result, skipped = build(a.clones, a.org, a.observed_on)
    for family, doc in result.items():
        if family == 'assoc':
            print('assoc: preserved Registry snapshot; use the site build to verify it')
            continue
        text = json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
        path = a.out / f'{family}.json'
        if a.check:
            if not path.exists() or path.read_text() != text:
                sys.exit(f'{path} is stale')
        else:
            a.out.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        unverified = sum(e['digestStatus'] == 'unverified' for e in doc['entries'])
        print(f'{family}: {doc["count"]} entries, {unverified} unverified')
    if skipped:
        print(f'skipped (not a keyed dataset repo, private or no default branch): {len(skipped)}: {skipped}', file=sys.stderr)


if __name__ == '__main__':
    main()
