#!/usr/bin/env python3
"""Build catalogs/actors.json (ADR 0011).

Reads each member repository's default-branch commit, visibility and license from GitHub
(read-only GraphQL) and hashes a fixed identity-file list from that pinned commit over
raw.githubusercontent.com. Copies no repository content and executes nothing from the
repositories. Membership is a reviewed declaration kept in the catalog itself: a refresh keeps
the repositories already listed; `--add NAME` lists a new one.

    build_actor_catalog.py [--add NAME ...] [--observed-on YYYY-MM-DD] [--out catalogs/actors.json]
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = 'cloud-itonami'
SCHEMA_VERSION = 'itonami.actor-sources.v1'
METHOD = ('GitHub GraphQL default-branch commit, visibility and license; payload sha256 read from the pinned '
          'commit over raw.githubusercontent.com. Repository content is not copied and nothing is executed.')
PAYLOAD = ['README.md', 'AGENTS.md', 'manifest.edn', 'identity.edn', 'actor.edn', 'kotoba.app.edn',
           'did.json', 'MATURITY.md', 'repository-contracts.edn']
DID = re.compile(r'did:web:[A-Za-z0-9._:%-]+')
STEM_PREFIX = re.compile(r'^(app-itonami-)')
KEY_ORDER = ['id', 'name', 'repository', 'commit', 'visibility', 'archived', 'license', 'kind', 'keys',
             'payload', 'digestStatus', 'status', 'authority']


def gh_repo(name):
    q = ('query($o:String!,$n:String!){repository(owner:$o,name:$n){visibility isArchived isFork description '
         'licenseInfo{spdxId} defaultBranchRef{target{... on Commit{oid}}}}}')
    for attempt in range(5):
        p = subprocess.run(['gh', 'api', 'graphql', '-f', f'query={q}', '-f', f'o={ORG}', '-f', f'n={name}'],
                           capture_output=True, text=True)
        if p.returncode == 0:
            return json.loads(p.stdout)['data']['repository']
        time.sleep(2 + attempt * 2)
    raise SystemExit(f'GitHub lookup failed: {name}\n{p.stderr[:200]}')


def raw(name, commit, path):
    url = f'https://raw.githubusercontent.com/{ORG}/{name}/{commit}/{path}'
    for attempt in range(3):
        try:
            return urllib.request.urlopen(url, timeout=30).read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            time.sleep(1 + attempt)
    raise SystemExit(f'fetch failed: {url}')


def stem(name):
    s = STEM_PREFIX.sub('', name)
    s = re.sub(r'^actor-', '', s)
    return re.sub(r'-(actor|lexicon|contracts|instrument|boundary|aozora|west)$', '', s) or s


def entry(name, observed):
    meta = gh_repo(name)
    if meta['visibility'] != 'PUBLIC' or meta['isFork']:
        print(f'skipped (not a public non-fork repository): {name}', file=sys.stderr)
        return None
    commit = meta['defaultBranchRef']['target']['oid']
    payload, did = [], None
    for path in PAYLOAD:
        body = raw(name, commit, path)
        if body is None:
            continue
        payload.append({'path': path, 'sha256': hashlib.sha256(body).hexdigest()})
        if did is None and path != 'README.md' and path != 'AGENTS.md':
            m = DID.search(body.decode('utf-8', 'replace'))
            did = m.group(0).rstrip(':') if m else None
    keys = {'actor': stem(name)}
    if did:
        keys['did'] = did
    desc = meta.get('description') or ''
    return {
        'id': 'actor/' + STEM_PREFIX.sub('', name),
        'repository': f'{ORG}/{name}',
        'commit': commit,
        'visibility': 'public',
        'archived': bool(meta['isArchived']),
        'license': (meta.get('licenseInfo') or {}).get('spdxId') or 'NOASSERTION',
        'kind': 'persona-loop' if 'co-scientist' in desc else 'actor',
        'keys': keys,
        'payload': payload,
        'digestStatus': 'verified' if payload else 'unverified',
        'status': 'repository-owned',
        'authority': {'grants': False, 'default': 'blocked'},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--add', nargs='*', default=[])
    ap.add_argument('--observed-on', default=date.today().isoformat())
    ap.add_argument('--out', default=str(ROOT / 'catalogs/actors.json'))
    args = ap.parse_args()
    out = Path(args.out)
    names = [e['repository'].split('/', 1)[1] for e in json.loads(out.read_text())['entries']] if out.exists() else []
    names = sorted(set(names) | set(args.add))
    entries = [e for e in (entry(n, args.observed_on) for n in names) if e]
    doc = {'schemaVersion': SCHEMA_VERSION, 'observedOn': args.observed_on, 'method': METHOD,
           'count': len(entries), 'entries': entries}
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
    print(f'wrote {len(entries)} entries to {out}')


if __name__ == '__main__':
    sys.exit(main())
