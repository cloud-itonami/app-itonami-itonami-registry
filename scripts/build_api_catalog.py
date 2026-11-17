#!/usr/bin/env python3
"""Build the api entries and their classification catalog (ADR 0005).

    build_api_catalog.py --clones DIR [--refresh] [--observed-on YYYY-MM-DD] [--check]

Writes
    apis/<id>/manifest.json            one first-class `api` entry per vendor-compatible API shape
    catalogs/api-classification.json   every selected repository, classified, with a reason

Selection: the public kotoba-lang repositories named `com-*`, `cloud-*` or with a dotted
(reverse-domain) name — the AWAI-59 target set. Private repositories are counted, never named.

Pins. `--refresh` lists the organization and reads each default-branch head with read-only
GitHub GraphQL, then records those commits. Without `--refresh` the commits already recorded in
catalogs/api-classification.json are reused, so `--check` is reproducible offline while the
owning repositories keep moving. Files are always read from the pinned commit object in a local
clone (`--clones`), never from a working tree; a commit object that is absent locally makes the
row `unclassified` rather than guessed. Nothing from the repositories is executed or copied
beyond the manifest fields listed in ADR 0005.

Relations to itonami dapps (implementedBy / consumedBy) come from the curated
catalogs/api-relations.json and are merged into the generated entries.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ORG = 'kotoba-lang'
CLASSIFICATION = 'catalogs/api-classification.json'
RELATIONS = 'catalogs/api-relations.json'
ORIGINS = 'catalogs/origin-domains.json'
COMPAT_SOURCES = 'catalogs/compat-sources.json'
REGISTRY = 'cloud-itonami/app-itonami-itonami-registry'
SCHEMA_VERSION = 'itonami.api-classification.v1'
METHOD = ('GitHub GraphQL default-branch commit, visibility, archive state and license (read-only), '
          'recorded as the pin; manifest.json and the digested files are read from the pinned commit '
          'object in a local clone. A missing commit object, manifest or API shape is recorded as '
          'unclassified with its reason, never inferred from the name or README.')
API_KINDS = {'compat', 'client'}
METHODS = {'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'}
ID = re.compile(r'^[a-z0-9][a-z0-9.-]{0,99}$')

REASONS = {
    'commit-not-available-locally': 'The pinned commit object is not in a local clone, so no file could be read or digested.',
    'dataset-snapshot-no-api-manifest': 'A DataLad dataset of an external API\'s responses, not an API shape. Candidate for a dataset-source catalog (ADR 0004) after its own review.',
    'connector-contract-no-api-manifest': 'A connector contract (connector.edn) with tools and OAuth scopes but no API-shape manifest. Candidate for an MCP or tool reference after review.',
    'no-api-manifest': 'No manifest.json at the pinned commit. The README describes a client library, codec, driver or service surface; a README is not parsed into an API shape.',
    'malformed-manifest': 'manifest.json at the pinned commit is not valid JSON or its routes are malformed.',
    'unsupported-manifest-kind': 'manifest.json declares a kind other than compat or client.',
    'manifest-without-api-shape': 'manifest.json has no capabilities.api.routes or no entities.',
    'registry-marker-needs-review': 'A skill or profile marker is present; skills and profiles are registered by a reviewed pull request, not by this generator.',
    'private-repository': 'A private repository: counted here, but its name and contents are not published.',
}


def family(name):
    if name.startswith('com-'):
        return 'com'
    if name.startswith('cloud-'):
        return 'cloud'
    if '.' in name and not name.startswith('.'):
        return 'dot'
    return None


def gh_json(args):
    return json.loads(subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout)


def remote_state(names):
    """{name: {commit, license, archived, private}} via batched read-only GraphQL."""
    out = {}
    for i in range(0, len(names), 40):
        chunk = names[i:i + 40]
        body = ' '.join(
            f'r{j}: repository(owner: "{ORG}", name: "{n}") {{ name isArchived isPrivate '
            f'licenseInfo {{ spdxId }} defaultBranchRef {{ target {{ oid }} }} }}'
            for j, n in enumerate(chunk))
        data = gh_json(['api', 'graphql', '-f', f'query=query {{ {body} }}'])['data']
        for r in data.values():
            if r and r['defaultBranchRef']:
                out[r['name']] = {'commit': r['defaultBranchRef']['target']['oid'],
                                  'license': (r['licenseInfo'] or {}).get('spdxId') or 'NOASSERTION',
                                  'archived': r['isArchived'], 'private': r['isPrivate']}
    return out


def observe():
    """Fresh pins from GitHub for the selected families."""
    listing = gh_json(['repo', 'list', ORG, '--limit', '10000', '--json', 'name'])
    names = sorted(r['name'] for r in listing if family(r['name']))
    state = remote_state(names)
    public = {n: s for n, s in state.items() if not s['private']}
    private = sorted(n for n, s in state.items() if s['private'])
    no_branch = sorted(set(names) - set(state))
    return public, private, no_branch


def recorded(root):
    """Pins already recorded in the classification catalog."""
    doc = json.loads((root / CLASSIFICATION).read_text())
    public = {e['repository'].split('/', 1)[1]: {'commit': e['commit'], 'license': e['license'],
                                                 'archived': e['archived'], 'private': False}
              for e in doc['entries']}
    return public, doc['counts']['privateOmitted'], doc['observedOn']


def git(clone, *args):
    return subprocess.run(['git', '-C', str(clone), *args], capture_output=True)


def blob(clone, commit, path):
    r = git(clone, 'show', f'{commit}:{path}')
    return r.stdout if r.returncode == 0 else None


def tree(clone, commit):
    r = git(clone, 'ls-tree', '-r', '--name-only', '-z', commit)
    return [p for p in r.stdout.decode().split('\0') if p] if r.returncode == 0 else None


def has_commit(clone, commit):
    return clone.is_dir() and git(clone, 'cat-file', '-e', f'{commit}^{{commit}}').returncode == 0


def host(url):
    try:
        return urlparse(url).hostname if isinstance(url, str) and url.startswith('https://') else None
    except ValueError:
        return None


def safe_path(p):
    return isinstance(p, str) and re.fullmatch(r'[A-Za-z0-9_.][A-Za-z0-9_./-]*', p) and '..' not in p.split('/')


def routes_of(api):
    routes = api.get('routes')
    if not isinstance(routes, list) or not routes:
        return None
    out = []
    for r in routes:
        if not (isinstance(r, dict) and r.get('method') in METHODS and isinstance(r.get('path'), str)
                and r['path'].startswith('/') and isinstance(r.get('op'), str)):
            raise ValueError('malformed route')
        out.append({'method': r['method'], 'path': r['path'], 'op': r['op']})
    return out


def strings(value):
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def load_internalized(root):
    """{name: origin commit} and the registry commit for compat actors whose origin repository was
    retired into compat/<name>/ (ADR 0006); their pins point at that registry commit."""
    path = root / COMPAT_SOURCES
    if not path.exists():
        return {}, None
    doc = json.loads(path.read_text())
    if not doc.get('originRetired'):
        return {}, None
    return {s['slug']: s['commit'] for s in doc['sources']}, doc['registryCommit']


def api_entry(name, pin, manifest, files, relations, origins=None, internal=None):
    api = (manifest.get('capabilities') or {}).get('api') or {}
    routes = routes_of(api)
    kind = manifest['kind']
    entry_api = {'kind': kind, 'tier': manifest.get('tier'), 'style': api.get('type'),
                 'entities': manifest['entities'], 'routeCount': len(routes), 'routes': routes}
    if isinstance(api.get('endpointCount'), int):
        entry_api['declaredEndpointCount'] = api['endpointCount']
    recorded_origin = (origins or {}).get(name)
    if recorded_origin:
        origin = {'status': 'recorded', 'domain': recorded_origin['domain'],
                  'reverseDomain': recorded_origin['reverseDomain'], 'record': ORIGINS,
                  'nameMatchesDomain': recorded_origin['nameMatchesDomain']}
    else:
        origin = {'status': 'unverified'}
    vendor = manifest.get('verified') or {}
    if kind == 'compat' and vendor.get('source'):
        entry_api['vendorSource'] = {'declared': vendor['source'], 'verifiedAt': vendor.get('verifiedAt'),
                                     'resources': vendor.get('resources') or [], 'enums': vendor.get('enums') or {},
                                     'basis': 'claimed-by-source-manifest'}
        origin['sourceHost'] = host(vendor['source'])
    upstream = manifest.get('upstream') or {}
    if kind == 'client' and upstream:
        entry_api['upstream'] = {k: upstream[k] for k in ['vendor', 'api', 'docs', 'verifiedAt', 'verifiedAgainst'] if isinstance(upstream.get(k), str)}
        origin['sourceHost'] = host(upstream.get('api'))
    origin = {k: v for k, v in origin.items() if v is not None}
    entry_api['origin'] = origin
    entry_api = {k: v for k, v in entry_api.items() if v is not None}
    actor = {k: manifest[k] for k in ['handle', 'did', 'runtime', 'exec', 'wasmCid', 'wasmProvenance', 'schema']
             if isinstance(manifest.get(k), str)}
    actor['basis'] = 'asserted-by-source-manifest'
    rel = relations.get(name, {})
    version = '1.0.0+' + pin['commit'][:12]  # always the origin commit, also once internalized
    overlay = {k: v for k, v in [('relations', rel), ('origin', recorded_origin)] if v}
    if overlay:  # curated data merged into the entry changes its version too
        version += '.x' + hashlib.sha256(json.dumps(overlay, sort_keys=True).encode()).hexdigest()[:8]
    tags = [kind] + ([manifest['tier']] if isinstance(manifest.get('tier'), str) else [])
    entry = {
        'schemaVersion': '1', 'type': 'api', 'id': name,
        'name': manifest.get('title') if isinstance(manifest.get('title'), str) and manifest['title'] else name,
        'version': version,
        'description': manifest.get('description') if isinstance(manifest.get('description'), str) and manifest['description'] else f'{kind} API shape declared by {ORG}/{name}',
        'author': ORG, 'license': pin['license'], 'tags': tags,
        'source': (f"https://github.com/{REGISTRY}/tree/{internal}/compat/{name}" if internal
                   else f"https://github.com/{ORG}/{name}/tree/{pin['commit']}"),
        'compatibility': {'hermes': 'none', 'itonami': '*'},
        'api': entry_api,
        'actor': actor,
        'pin': ({'repository': REGISTRY, 'commit': internal, 'path': f'compat/{name}', 'visibility': 'public',
                 'archived': False, 'digestStatus': 'verified', 'files': files,
                 'origin': {'repository': f'{ORG}/{name}', 'commit': pin['commit'], 'archived': True, 'state': 'deleted'}}
                if internal else
                {'repository': f'{ORG}/{name}', 'commit': pin['commit'], 'visibility': 'public',
                 'archived': pin['archived'], 'digestStatus': 'verified', 'files': files}),
        'status': {'shape': 'declared-by-source-manifest',
                   'vendorConformance': 'claimed-by-source' if 'vendorSource' in entry_api or 'upstream' in entry_api else 'not-claimed',
                   'runtimeQualified': False, 'artifactVerified': False, 'execution': 'none',
                   'authority': {'grants': False, 'default': 'blocked'},
                   'validation': {'live': False, 'catalog': True}},
        'relations': {'implementedBy': rel.get('implementedBy', []), 'consumedBy': rel.get('consumedBy', [])},
    }
    return entry


def classify(name, pin, clones, relations, origins=None, internal=None, root=ROOT):
    """(row, entry-or-None) for one public repository at its pinned commit."""
    row = {'repository': f'{ORG}/{name}', 'family': family(name), 'commit': pin['commit'],
           'license': pin['license'], 'archived': pin['archived']}
    clone, rev, prefix = clones / name, pin['commit'], ''
    if internal:  # retired origin: read the same files from compat/<name>/ at the registry commit
        clone, rev, prefix = root, internal, f'compat/{name}/'
        row['retiredTo'] = {'repository': REGISTRY, 'commit': internal, 'path': f'compat/{name}'}
    if not has_commit(clone, rev):
        return dict(row, **{'class': 'unclassified', 'reason': 'commit-not-available-locally'}), None
    files = tree(clone, f'{rev}:{prefix.rstrip("/")}' if prefix else rev) or []
    markers = sorted(p for p in files if re.search(r'(^|/)SKILL\.md$', p) or re.search(r'(^|/)hermes/profiles/[^/]+/SOUL\.md$', p)
                     or p.endswith('.itonami/profile.edn'))
    raw = blob(clone, rev, prefix + 'manifest.json')
    if raw is None:
        if markers:
            return dict(row, **{'class': 'unclassified', 'reason': 'registry-marker-needs-review', 'evidence': markers[:5]}), None
        top = {p.split('/', 1)[0] for p in files}
        if '.datalad' in top:
            return dict(row, **{'class': 'unclassified', 'reason': 'dataset-snapshot-no-api-manifest', 'evidence': ['.datalad']}), None
        if 'connector.edn' in top:
            return dict(row, **{'class': 'unclassified', 'reason': 'connector-contract-no-api-manifest', 'evidence': ['connector.edn']}), None
        return dict(row, **{'class': 'unclassified', 'reason': 'no-api-manifest'}), None
    try:
        manifest = json.loads(raw)
        if not isinstance(manifest, dict):
            raise ValueError('not an object')
    except ValueError:
        return dict(row, **{'class': 'unclassified', 'reason': 'malformed-manifest', 'evidence': ['manifest.json']}), None
    if manifest.get('kind') not in API_KINDS:
        return dict(row, **{'class': 'unclassified', 'reason': 'unsupported-manifest-kind', 'evidence': ['manifest.json']}), None
    api = (manifest.get('capabilities') or {}).get('api')
    if not isinstance(api, dict) or not strings(manifest.get('entities')) or not manifest['entities']:
        return dict(row, **{'class': 'unclassified', 'reason': 'manifest-without-api-shape', 'evidence': ['manifest.json']}), None
    try:
        if routes_of(api) is None:
            return dict(row, **{'class': 'unclassified', 'reason': 'manifest-without-api-shape', 'evidence': ['manifest.json']}), None
    except ValueError:
        return dict(row, **{'class': 'unclassified', 'reason': 'malformed-manifest', 'evidence': ['manifest.json']}), None
    if not ID.fullmatch(name):
        return dict(row, **{'class': 'unclassified', 'reason': 'malformed-manifest', 'evidence': ['repository name']}), None
    digested = []
    wanted = ['manifest.json', 'openapi.json', 'README.md']
    if safe_path(manifest.get('schema')):
        wanted.append(manifest['schema'])
    for path in sorted(set(wanted)):
        data = blob(clone, rev, prefix + path)
        if data is not None:
            digested.append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    entry = api_entry(name, pin, manifest, digested, relations, origins, internal)
    return dict(row, **{'class': 'api', 'entry': f'api/{name}'}), entry


def load_origins(root):
    """{api id: origin fact} from the public origin-domain extract (scripts/extract_origin_domains.py)."""
    path = root / ORIGINS
    if not path.exists():
        return {}
    return {e['api']: e for e in json.loads(path.read_text())['entries']}


def load_relations(root):
    doc = json.loads((root / RELATIONS).read_text())
    out = {}
    for r in doc['relations']:
        if r['api'] in out:
            raise ValueError(f"Duplicate api relation: {r['api']}")
        out[r['api']] = {k: sorted(r.get(k, [])) for k in ['implementedBy', 'consumedBy'] if r.get(k)}
    return out


def build(root, clones, refresh, observed_on):
    relations = load_relations(root)
    origins = load_origins(root)
    if refresh:
        public, private, no_branch = observe()
        private_count = len(private)
        if no_branch:
            print(f'not classified (no default branch, unreadable): {no_branch}', file=sys.stderr)
    else:
        public, private_count, observed_on = recorded(root)
    retired, registry_commit = load_internalized(root)
    prior = {e['repository'].split('/', 1)[1]: e for e in json.loads((root / CLASSIFICATION).read_text())['entries']}
    for name, commit in retired.items():  # origin repositories no longer exist (or are about to): pin from the record
        public[name] = {'commit': commit, 'license': prior[name]['license'], 'archived': True, 'private': False}
    rows, entries = [], {}
    for name in sorted(public):
        row, entry = classify(name, public[name], clones, relations, origins,
                              registry_commit if name in retired else None, root)
        rows.append(row)
        if entry:
            entries[name] = entry
    unknown = sorted(set(relations) - set(entries))
    if unknown:
        raise ValueError(f'Relations name no api entry: {unknown}')
    orphan = sorted(set(origins) - set(entries))
    if orphan:
        raise ValueError(f'Origin extract names no api entry: {orphan}')
    by_class = {c: 0 for c in ['api', 'skill', 'profile', 'bot', 'unclassified']}
    by_reason, by_family = {}, {}
    for r in rows:
        by_class[r['class']] += 1
        if r['class'] == 'unclassified':
            by_reason[r['reason']] = by_reason.get(r['reason'], 0) + 1
        by_family[r['family']] = by_family.get(r['family'], 0) + 1
    by_class['unclassified'] += private_count
    if private_count:
        by_reason['private-repository'] = private_count
    doc = {'schemaVersion': SCHEMA_VERSION, 'organization': ORG, 'observedOn': observed_on, 'method': METHOD,
           'selection': 'Public and private repositories of the organization named com-*, cloud-* or with a dotted reverse-domain name (the AWAI-59 target set). Private repositories are counted only.',
           'counts': {'total': len(rows) + private_count, 'public': len(rows), 'privateOmitted': private_count,
                      'publicByFamily': dict(sorted(by_family.items())), 'byClass': by_class,
                      'unclassifiedByReason': dict(sorted(by_reason.items(), key=lambda kv: (-kv[1], kv[0])))},
           'reasons': {k: REASONS[k] for k in sorted(by_reason)},
           'entries': rows}
    return doc, entries


def render(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Build apis/ and catalogs/api-classification.json (ADR 0005)')
    ap.add_argument('--clones', type=Path, required=True, help='directory holding local clones named by repository')
    ap.add_argument('--refresh', action='store_true', help='re-observe pins from GitHub instead of reusing recorded ones')
    ap.add_argument('--observed-on', default=date.today().isoformat())
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--check', action='store_true', help='fail if files on disk differ from a fresh build')
    a = ap.parse_args(argv)
    doc, entries = build(a.root, a.clones, a.refresh, a.observed_on)
    expected = {a.root / CLASSIFICATION: render(doc)}
    expected.update({a.root / 'apis' / n / 'manifest.json': render(e) for n, e in entries.items()})
    present = set((a.root / 'apis').glob('*/*')) if (a.root / 'apis').exists() else set()
    stale = sorted(p for p in present if p not in expected)
    if a.check:
        bad = [str(p.relative_to(a.root)) for p, t in expected.items() if not p.exists() or p.read_text() != t]
        if bad or stale:
            sys.exit(f'api catalog is stale ({len(bad)} differ, {len(stale)} extra); run scripts/build_api_catalog.py: {(bad + [str(p) for p in stale])[:5]}')
    else:
        for p in stale:
            p.unlink()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()
        for p, t in expected.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text() != t:
                p.write_text(t)
    c = doc['counts']
    print(f"{'Verified' if a.check else 'Built'} {len(entries)} api entries; {c['total']} repositories classified "
          f"({c['byClass']}; unclassified reasons {c['unclassifiedByReason']}; private {c['privateOmitted']})")


if __name__ == '__main__':
    main()
