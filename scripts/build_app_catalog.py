#!/usr/bin/env python3
"""Build catalogs/apps.json (ADR 0015).

Reads each member repository's default-branch commit, visibility and license from GitHub
(read-only GraphQL) and hashes a fixed identity-file list from that pinned commit over
raw.githubusercontent.com. Copies no repository content and executes nothing from the
repositories. Membership is a reviewed declaration kept in the catalog itself: a refresh keeps
the repositories already listed; `--add NAME` lists a new one. Repository names are the
redirect-resolved canonical owner/name (repo_redirects.canonical, KOTOBA-159): `--add`
takes a bare name under the default owner and is canonicalized.

    build_app_catalog.py [--add NAME ...] [--observed-on YYYY-MM-DD] [--out catalogs/apps.json]
"""
import argparse
import concurrent.futures as cf
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

import repo_redirects
import skip_sources

ROOT = Path(__file__).resolve().parents[1]
ORG = 'cloud-itonami'
SCHEMA_VERSION = 'itonami.app-sources.v1'
METHOD = ('GitHub GraphQL default-branch commit, visibility and license; payload sha256 read from the pinned '
          'commit over raw.githubusercontent.com. Repository content is not copied and nothing is executed.')
PAYLOAD = ['README.md', 'AGENTS.md', 'LICENSE', 'NOTICE', 'MATURITY.md', 'manifest.edn', 'kotoba.app.edn', 'package.json',
           'wrangler.jsonc', 'wrangler.toml', 'shadow-cljs.edn', 'deps.edn', 'nbb.edn', 'cljk-origin.edn']
STEM_PREFIX = re.compile(r'^(app-itonami-)')


def gh_repo(repository):
    owner, name = repository.split('/', 1)
    q = ('query($o:String!,$n:String!){repository(owner:$o,name:$n){visibility isArchived isFork '
         'licenseInfo{spdxId} defaultBranchRef{target{... on Commit{oid}}}}}')
    for attempt in range(5):
        p = subprocess.run(['gh', 'api', 'graphql', '-f', f'query={q}', '-f', f'o={owner}', '-f', f'n={name}'],
                           capture_output=True, text=True)
        if p.returncode == 0:
            return json.loads(p.stdout)['data']['repository']
        time.sleep(2 + attempt * 2)
    raise SystemExit(f'GitHub lookup failed: {repository}\n{p.stderr[:200]}')


def raw(repository, commit, path):
    url = f'https://raw.githubusercontent.com/{repository}/{commit}/{path}'
    for attempt in range(4):
        try:
            return urllib.request.urlopen(url, timeout=30).read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1 + attempt)
    raise SystemExit(f'fetch failed: {url}')


def entry(repository):
    repository = repo_redirects.canonical(repository)
    meta = gh_repo(repository)
    if meta['visibility'] != 'PUBLIC' or meta['isFork']:
        print(f'skipped (not a public non-fork repository): {repository}', file=sys.stderr)
        return None
    commit = meta['defaultBranchRef']['target']['oid']
    payload = []
    for path in PAYLOAD:
        body = raw(repository, commit, path)
        if body is None:
            continue
        payload.append({'path': path, 'sha256': hashlib.sha256(body).hexdigest()})
    have = {p['path'] for p in payload}
    if have & {'wrangler.jsonc', 'wrangler.toml'}:
        kind = 'worker-app'
    elif 'kotoba.app.edn' in have:
        kind = 'kotoba-app'
    elif have & {'package.json', 'shadow-cljs.edn'}:
        kind = 'js-app'
    elif 'deps.edn' in have:
        kind = 'clj-app'
    else:
        kind = 'other'
    keys = {'app': STEM_PREFIX.sub('', repository.split('/', 1)[1])}
    return {
        'id': 'app/' + keys['app'],
        'repository': repository,
        'commit': commit,
        'visibility': 'public',
        'archived': bool(meta['isArchived']),
        'license': (meta.get('licenseInfo') or {}).get('spdxId') or 'NOASSERTION',
        'kind': kind,
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
    ap.add_argument('--out', default=str(ROOT / 'catalogs/apps.json'))
    args = ap.parse_args()
    out = Path(args.out)
    prior = json.loads(out.read_text())['entries'] if out.exists() else []
    names = sorted({repo_redirects.canonical(e['repository']) for e in prior} |
                   {repo_redirects.canonical(f'{ORG}/{n}') for n in args.add})
    skipped = skip_sources.load(ROOT)
    kept = {e['repository']: e for e in prior if e['repository'] in skipped}
    for repository in sorted(kept):
        print(skip_sources.note(repository, skipped[repository], 'refresh; entry kept unchanged'), file=sys.stderr)
    kept = {repo_redirects.canonical(e['repository']):
            dict(e, repository=repo_redirects.canonical(e['repository'])) for e in kept.values()}
    fetch = [r for r in names if r not in skipped]
    with cf.ThreadPoolExecutor(6) as ex:
        built = dict(zip(fetch, ex.map(entry, fetch)))
    entries = [e for e in (kept.get(r) or built.get(r) for r in names) if e]
    doc = {'schemaVersion': SCHEMA_VERSION, 'observedOn': args.observed_on, 'method': METHOD,
           'count': len(entries), 'entries': entries}
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
    print(f'wrote {len(entries)} entries to {out}')


if __name__ == '__main__':
    sys.exit(main())
