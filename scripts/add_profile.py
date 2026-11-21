#!/usr/bin/env python3
"""Register an Itonami profile owned by another repository (ADR 0002).

    python scripts/add_profile.py --checkout ~/github/cloud-itonami/app-itonami-cloud-itonami-app \
        --repository cloud-itonami/app-itonami-cloud-itonami-app --commit <sha> \
        --path hermes/profiles/itonami-eng [--id itonami-eng] [--source-ref itonami-app]

Reads the profile folder from git objects at the commit (never the working
tree), refuses credentials/memories/state, and writes profiles/<id>/manifest.json,
profiles/<id>/itonami.json and the file hashes into catalogs/sources.json. The
profile files themselves stay in the owning repository.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml

from profile_tree import allowed, tree_checksum

ROOT = Path(__file__).resolve().parents[1]


def git(checkout, *args):
    return subprocess.run(['git', '-C', str(checkout), *args], check=True, capture_output=True).stdout


def profile_files(checkout, commit, path, exclude=()):
    names = git(checkout, 'ls-tree', '-r', '-z', '--name-only', commit, '--', path).decode().split('\0')
    files, refused = [], []
    for name in filter(None, names):
        rel = name[len(path) + 1:]
        if rel.rsplit('/', 1)[-1] in exclude:
            continue
        if not allowed(rel):
            refused.append(rel)
            continue
        data = git(checkout, 'show', f'{commit}:{name}')
        files.append({'path': rel, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'data': data})
    if refused:
        raise SystemExit(f'refused non-profile files in {path}: {refused}')
    if not any(f['path'] == 'SOUL.md' for f in files):
        raise SystemExit(f'{path} has no SOUL.md; not a profile')
    return files


def register_targeted(repository, commit, entry):
    """Record a registration on a targeted public source row (ADR 0002 profile
    type); the row is created at this commit when absent. Public repositories
    only — private sources are refused by validate.py."""
    import time
    path = ROOT / 'catalogs/targeted-public-sources.json'
    data = json.loads(path.read_text())
    reg = {'entry': entry, 'sourceCommit': commit}
    row = next((r for r in data['sources'] if r['repository'] == repository), None)
    if row is None:
        row = {'repository': repository, 'commit': commit, 'visibility': 'public',
               'reviewedOn': time.strftime('%Y-%m-%d'),
               'reviewBasis': 'Targeted review: GitHub repository metadata confirms public '
                              'visibility; the profile folder was inspected for registration '
                              'material. Targeted review, not an organization-wide survey.',
               'registrations': []}
        data['sources'].append(row)
    if row['commit'] != commit:
        raise SystemExit(f'{repository} is a targeted source pinned to {row["commit"]}; use the same commit')
    if reg not in row['registrations']:
        row['registrations'].append(reg)
        row['registrations'].sort(key=lambda r: (r['entry'], r['sourceCommit']))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--checkout', required=True)
    p.add_argument('--repository', required=True)
    p.add_argument('--commit', required=True)
    p.add_argument('--path', required=True)
    p.add_argument('--id')
    p.add_argument('--source-ref', default=None)
    p.add_argument('--version', default='0.1.0')
    p.add_argument('--exclude', action='append', default=[],
                   help='file basename to drop from the pin (e.g. secrets.edn); stays in the owning repository unpinned')
    a = p.parse_args()
    checkout = Path(a.checkout).expanduser()
    commit = git(checkout, 'rev-parse', a.commit + '^{commit}').decode().strip()
    pid = a.id or a.path.rstrip('/').rsplit('/', 1)[-1]
    files = profile_files(checkout, commit, a.path.rstrip('/'), exclude=set(a.exclude))
    meta = {}
    for f in files:
        if f['path'] == 'profile.yaml':
            meta = yaml.safe_load(f['data']) or {}
    soul = next(f['data'] for f in files if f['path'] == 'SOUL.md').decode('utf-8', 'replace')
    lines = [l.strip() for l in soul.splitlines() if l.strip()]
    heading = next((l.strip('# ').strip() for l in lines if l.startswith('#')), pid)
    prose = next((l for l in lines if not l.startswith(('#', '-', '|', '>', '```'))), '')
    description = str(meta.get('description') or '').strip()
    if len(description) < 24:
        # profile.yaml often carries only the name; the SOUL says what it is.
        description = ' — '.join(x for x in [heading, prose] if x) or pid
    ref = a.source_ref or a.repository.split('/')[-1]
    source = f'https://github.com/{a.repository}/tree/{commit}'
    listed = [{k: f[k] for k in ('path', 'sha256', 'bytes')} for f in files]
    manifest = {
        'schemaVersion': '1', 'type': 'profile', 'id': pid, 'name': pid,
        'version': a.version, 'description': description[:500], 'author': a.repository.split('/')[0],
        'source': source, 'compatibility': {'hermes': '*', 'itonami': '*'},
        'profile': {'layout': 'hermes-profile', 'repository': a.repository, 'commit': commit,
                    'path': a.path.rstrip('/'), 'checksum': tree_checksum(listed), 'files': listed},
    }
    skills = sorted({f['path'].split('/')[1] for f in files if f['path'].startswith('skills/')})
    side = {
        'schemaVersion': 'itonami.entry.v1', 'sourceRefs': [ref],
        'useWhen': f'Install as a Bot (Itonami profile) or as a Hermes profile: {description[:200]}',
        'avoidWhen': 'Expecting credentials, accounts, memories or an enabled schedule to come with it.',
        'inputs': {'owner': 'the installing organization binds accounts and grants'},
        'outputs': {'profile': 'Hermes profile files at the pinned commit', 'skills': ', '.join(skills) or 'none'},
        'effects': ['profile-install'],
        'authority': {'grants': False, 'default': 'blocked',
                      'binding': 'The installing owner rebinds accounts, connector grants, wallet signer and approval policy; cron arrives disabled.'},
        'validation': {'catalog': 'schema-checked', 'runtime': 'not qualified by publication', 'live': False},
        'compatibilityNote': 'Itonami profile = Hermes profile layout. Files stay in the owning repository at the pinned commit; verify the tree checksum before use.',
        'roleKind': 'profile',
    }
    folder = ROOT / 'profiles' / pid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (folder / 'itonami.json').write_text(json.dumps(side, ensure_ascii=False, indent=2) + '\n')
    sources_path = ROOT / 'catalogs/sources.json'
    sources = json.loads(sources_path.read_text())
    by_id = {s['id']: s for s in sources['sources']}
    entry = by_id.get(ref)
    if entry and entry['commit'] != commit:
        raise SystemExit(f'source ref {ref} is pinned to {entry["commit"]}; use the same commit or a new --source-ref')
    if not entry:
        entry = {'id': ref, 'repository': a.repository, 'commit': commit, 'files': []}
        sources['sources'].append(entry)
    have = {f['path'] for f in entry['files']}
    for f in files:
        rp = f"{a.path.rstrip('/')}/{f['path']}"
        if rp not in have:
            entry['files'].append({'path': rp, 'sha256': f['sha256'],
                                   'url': f'https://github.com/{a.repository}/blob/{commit}/{rp}'})
    entry['files'].sort(key=lambda f: f['path'])
    sources_path.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n')
    # The inventory records which registry entries each surveyed repository
    # contributes; validate.py checks it against every entry's provenance.
    inv_path = ROOT / 'catalogs/inventory.json'
    lines = inv_path.read_text().split('\n')
    prefix = f'    {{"repository": "{a.repository}"'
    at = next((i for i, l in enumerate(lines) if l.startswith(prefix)), None)
    if at is None:
        register_targeted(a.repository, commit, f'profile/{pid}')
        print(f'registered profile {pid} ({len(files)} files) from {a.repository}@{commit[:7]}')
        return
    # Rows are one line each (separators ',' and ': '); rewrite only this one.
    body = lines[at].strip()
    comma = body.endswith(',')
    row = json.loads(body.rstrip(','))
    reg = {'sourceCommit': commit, 'entry': f'profile/{pid}'}
    if reg not in row['registrations']:
        row['registrations'].append(reg)
        row['registrations'].sort(key=lambda r: (r['entry'], r['sourceCommit']))
    lines[at] = '    ' + json.dumps(row, ensure_ascii=False, separators=(',', ': ')) + (',' if comma else '')
    inv_path.write_text('\n'.join(lines))
    print(f'registered profile {pid} ({len(files)} files) from {a.repository}@{commit[:7]}')


if __name__ == '__main__':
    main()
