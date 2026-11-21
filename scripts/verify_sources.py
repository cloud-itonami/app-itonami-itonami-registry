#!/usr/bin/env python3
"""Read immutable GitHub files and compare provenance; requires authenticated gh."""
import ast
from concurrent.futures import ThreadPoolExecutor
import base64
import hashlib
import json
import subprocess
from pathlib import Path

import skip_sources

ROOT = Path(__file__).resolve().parents[1]


def fetch(repository, commit, path):
    response = json.loads(subprocess.check_output(
        ['gh', 'api', f'repos/{repository}/contents/{path}?ref={commit}'], timeout=30))
    if response.get('encoding') != 'base64':
        raise ValueError(f'Unsupported source encoding: {path}')
    return base64.b64decode(response['content'])


if __name__ == '__main__':
    sources = json.loads((ROOT / 'catalogs/sources.json').read_text())['sources']
    requests = {}
    for source in sources:
        for file in source['files']:
            key = (source['repository'], source['commit'], file['path'])
            requests[key] = file['sha256']
    reviews = json.loads((ROOT / 'catalogs/candidate-reviews.json').read_text())['reviews']
    for review in reviews:
        for file in review['evidence']:
            key = (review['repository'], review['commit'], file['path'])
            if key in requests and requests[key] != file['sha256']:
                raise ValueError('Candidate/source provenance digest mismatch')
            requests[key] = file['sha256']
    skipped = skip_sources.load(ROOT)
    held = sorted({k[0] for k in requests if k[0] in skipped})
    for repository in held:
        print(skip_sources.note(repository, skipped[repository], 'readback'))
    requests = {k: v for k, v in requests.items() if k[0] not in skipped}
    def checked_fetch(item):
        key, digest = item
        data = fetch(*key)
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'Source mismatch: {key[0]}/{key[2]}')
        return key, data
    with ThreadPoolExecutor(max_workers=4) as pool:
        fetched = dict(pool.map(checked_fetch, requests.items()))
    checked = sum(len(source['files']) for source in sources if source['repository'] not in skipped)
    # Literal AST inspection only: never imports plugin handlers or executes scans.
    zap = next(source for source in sources if source['id'] == 'zap-plugin')
    schema_bytes = fetched[(zap['repository'], zap['commit'], 'plugin/schemas.py')]
    descriptors = {}
    for node in ast.parse(schema_bytes).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ['ZAP_SCAN', 'ZAP_SCAN_ACTIVE', 'ZAP_SCAN_RULES'] for t in node.targets):
            native = ast.literal_eval(node.value)
            descriptors[native['name']] = native
    tools = json.loads((ROOT / 'catalogs/tools.json').read_text())['tools']
    indexed = {t['name']: t for t in tools if t['provider']['sourceRef'] == 'zap-plugin'}
    if descriptors.keys() != indexed.keys():
        raise ValueError('ZAP native/indexed descriptor identities differ')
    for name, native in descriptors.items():
        if native['description'] != indexed[name]['description'] or native['parameters'] != indexed[name]['inputSchema']:
            raise ValueError('ZAP native/indexed descriptor changed')
    provenance = json.loads((ROOT / 'schemas/hermes/provenance.json').read_text())
    for file in provenance['files']:
        data = fetch(provenance['repository'], provenance['commit'], file['upstreamPath'])
        if hashlib.sha256(data).hexdigest() != file['sha256']:
            raise ValueError(f"Upstream schema mismatch: {file['path']}")
    local = json.loads((ROOT / 'index.json').read_text())['entries']
    identities = {e['type'] + '/' + e['id'] for e in local}
    for registry in json.loads((ROOT / 'catalogs/external-registries.json').read_text())['registries']:
        upstream = json.loads(fetch(registry['repository'], registry['commit'], 'index.json'))
        upstream_ids = {e['type'] + '/' + e['id'] for e in upstream['entries']}
        if identities & upstream_ids:
            raise ValueError('Local catalog duplicates external entries')
        if not set(registry['entries']) <= upstream_ids:
            raise ValueError('External entry reference does not resolve')
    print(f'GitHub readback verified {checked} registered source-file references and {sum(len(r["evidence"]) for r in reviews)} candidate evidence references ({len(fetched)} unique files), {len(provenance["files"])} schemas, 3 native plugin descriptors and external references')
