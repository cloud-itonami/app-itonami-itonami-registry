#!/usr/bin/env python3
"""Classify every profile entry of this registry against its source repository
(ADR 0007).

    python3 scripts/profile_status.py --cache DIR [--homes homes.json] [--out FILE]
                                      [--jobs N] [--only-id ID] [--url-template T]

For each profiles/<id>/manifest.json it asks one question of the source
repository's DEFAULT BRANCH TIP: is the profile pinned here still what the owner
has? The answer is one of four states.

  current      the profile at the tip is the pinned one (same files, same checksum)
  behind       the repository has moved on: the files differ from the pin, the profile
               moved to another path, or the pinned commit is not on the default branch
  withdrawn    the repository is reachable but no profile is at the pinned path or at
               hermes/profiles/<id> any more
  unreachable  the repository cannot be fetched, or the pinned commit is not in it
  skipped      the repository is on catalogs/skip-sources.json (temporarily unreadable);
               it is not fetched and the registry entry is left unchanged

The states are derived. Nothing here edits a manifest, and a pin is immutable: an
archived repository still serves its pinned commit, so `current`, `behind` and
`withdrawn` are properties of the owner's tip, not of the pin's validity.

The comparison uses this registry's own definition (scripts/profile_tree.py): the
checksum is over the allowed files of the profile folder, by path relative to the
profile, so it does not depend on where the repository keeps the folder. A repository
is read through a partial bare clone (commits only; trees and blobs are fetched on
demand) kept in --cache, so a re-run only fetches what changed.

--homes is an optional JSON map {profile id -> "org/repo"} taken from the operational
binding (root manifest/agent-registry :home). When given, each record also says whether
that binding and this registry name the same repository.

--shared-only reports, offline and from the manifests alone, the repositories that hold
more than one profile (ADR 0008) against catalogs/shared-profile-repositories.json;
--findings-out writes them as JSON in either mode.

Needs git and, for the default URL template, ssh access to the repositories.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_tree import allowed, tree_checksum  # noqa: E402

import skip_sources

ROOT = Path(__file__).resolve().parents[1]
STATES = ('current', 'behind', 'withdrawn', 'unreachable', 'skipped')
SHARED_FILE = 'catalogs/shared-profile-repositories.json'
SHARED_SCHEMA = 'itonami.shared-repositories.v1'
SHARED_KINDS = ('fleet', 'maintainer')


def git(repo, *args, check=False):
    r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if check and r.returncode:
        raise RuntimeError(r.stderr.decode(errors='replace').strip()[:200])
    return r


def ensure_cache(repo_slug, cache, template):
    """Bare partial clone of the default branch (and the rest of the branches)."""
    d = Path(cache) / (repo_slug.replace('/', '__') + '.git')
    url = template.format(repo=repo_slug)
    if d.is_dir():
        r = git(d, 'fetch', '-q', 'origin', '+refs/heads/*:refs/heads/*', '--prune')
        return d, None if r.returncode == 0 else r.stderr.decode(errors='replace').strip()[:160]
    d.parent.mkdir(parents=True, exist_ok=True)
    for extra in (['--filter=tree:0'], []):
        r = subprocess.run(['git', 'clone', '-q', '--bare', *extra, url, str(d)], capture_output=True)
        if r.returncode == 0:
            return d, None
        subprocess.run(['rm', '-rf', str(d)])
    return None, r.stderr.decode(errors='replace').strip().splitlines()[-1][:160] if r.stderr else 'clone failed'


def profile_files(repo, ref, path):
    """[{'path','sha256'}] for the allowed files of the profile folder at ref."""
    out = git(repo, 'ls-tree', '-r', '-z', '--name-only', ref, '--', path).stdout.decode().split('\0')
    files = []
    for name in filter(None, out):
        rel = name[len(path) + 1:]
        if not allowed(rel):
            continue
        blob = git(repo, 'cat-file', 'blob', f'{ref}:{name}').stdout
        files.append({'path': rel, 'sha256': hashlib.sha256(blob).hexdigest()})
    return files


def classify(entry, repo_dir, load_error):
    rec = {'id': entry['id'], 'repository': entry['repository'], 'path': entry['path'],
           'pinnedCommit': entry['commit']}
    if repo_dir is None:
        return {**rec, 'state': 'unreachable', 'reason': 'repository not fetchable: ' + (load_error or '?')}
    r = git(repo_dir, 'rev-parse', '-q', '--verify', 'HEAD^{commit}')
    if r.returncode:
        return {**rec, 'state': 'unreachable', 'reason': 'repository has no default-branch tip'}
    tip = r.stdout.decode().strip()
    rec['tip'] = tip
    if git(repo_dir, 'cat-file', '-e', entry['commit'] + '^{commit}').returncode:
        return {**rec, 'state': 'unreachable', 'reason': 'pinned commit is not in the repository'}
    on_default = git(repo_dir, 'merge-base', '--is-ancestor', entry['commit'], tip).returncode == 0
    rec['pinOnDefaultBranch'] = on_default
    path, pid = entry['path'], entry['id']
    here = git(repo_dir, 'rev-parse', '-q', '--verify', f'{tip}:{path}')
    where = path
    if here.returncode:
        alt = f'hermes/profiles/{pid}'
        if alt != path and git(repo_dir, 'rev-parse', '-q', '--verify', f'{tip}:{alt}').returncode == 0:
            where = alt
        else:
            return {**rec, 'state': 'withdrawn',
                    'reason': f'no profile at {path} or at hermes/profiles/{pid} on the default branch'}
    rec['tipPath'] = where
    tip_tree = git(repo_dir, 'rev-parse', f'{tip}:{where}').stdout.decode().strip()
    pin_tree = git(repo_dir, 'rev-parse', '-q', '--verify', f"{entry['commit']}:{path}").stdout.decode().strip()
    if where == path and tip_tree == pin_tree and on_default:
        return {**rec, 'state': 'current', 'reason': 'same tree at the tip'}
    now = tree_checksum(profile_files(repo_dir, tip, where))
    same = now == entry['checksum']
    if same and where == path and on_default:
        return {**rec, 'state': 'current', 'reason': 'only files outside the pin differ'}
    if where != path:
        return {**rec, 'state': 'behind', 'reason': f'moved to {where}' + ('' if not same else ' (same files)')}
    if not on_default:
        return {**rec, 'state': 'behind', 'reason': 'pinned commit is not on the default branch'}
    return {**rec, 'state': 'behind', 'reason': 'files differ from the pin at the tip'}


def load_entries(root, only_id=None):
    entries = []
    for f in sorted(Path(root, 'profiles').glob('*/manifest.json')):
        m = json.loads(f.read_text())
        if only_id and m['id'] != only_id:
            continue
        p = m['profile']
        entries.append({'id': m['id'], 'repository': p['repository'], 'commit': p['commit'],
                        'path': p['path'], 'checksum': p['checksum']})
    return entries


def load_declared(root):
    """The declared exceptions to one-profile-one-repository (ADR 0008), validated for shape."""
    doc = json.loads(Path(root, SHARED_FILE).read_text())
    if doc.get('schemaVersion') != SHARED_SCHEMA or not isinstance(doc.get('repositories'), list):
        raise ValueError(f'{SHARED_FILE}: expected schemaVersion {SHARED_SCHEMA} and a repositories list')
    declared = {}
    for d in doc['repositories']:
        if set(d) != {'repository', 'kind', 'reason'}:
            raise ValueError(f'{SHARED_FILE}: entries need exactly repository, kind, reason: {d}')
        if d['kind'] not in SHARED_KINDS or not d['reason'].strip() or d['repository'].count('/') != 1:
            raise ValueError(f'{SHARED_FILE}: bad entry {d}')
        if d['repository'] in declared:
            raise ValueError(f"{SHARED_FILE}: duplicate {d['repository']}")
        declared[d['repository']] = d
    return declared


def shared_findings(entries, declared):
    """Offline, from the manifests alone (ADR 0008): repositories that hold several profiles."""
    by_repo = {}
    for e in entries:
        by_repo.setdefault(e['repository'], []).append(e['id'])
    out = []
    for repo, ids in sorted(by_repo.items()):
        d = declared.get(repo)
        if len(ids) > 1:
            out.append({'code': 'shared-repository' if d is None else 'shared-repository-declared',
                        'repository': repo, 'profiles': sorted(ids), 'kind': d and d['kind'],
                        'reason': d and d['reason']})
        elif d is not None:
            out.append({'code': 'declaration-without-sharing', 'repository': repo, 'profiles': ids})
    for repo in sorted(set(declared) - set(by_repo)):
        out.append({'code': 'declaration-unknown-repository', 'repository': repo, 'profiles': []})
    return out


def findings_summary(findings):
    c = Counter(f['code'] for f in findings)
    lines = ['shared-repository findings: ' + (', '.join(f'{k}={v}' for k, v in sorted(c.items())) or 'none')]
    for f in findings:
        if f['code'] != 'shared-repository-declared':
            lines.append(f"  {f['code']:31} {f['repository']} ({len(f['profiles'])} profiles)")
    return '\n'.join(lines)


def run(entries, cache, template, jobs, homes=None, skipped=None):
    skipped = skip_sources.load() if skipped is None else skipped
    held = [e for e in entries if e['repository'] in skipped]
    entries = [e for e in entries if e['repository'] not in skipped]
    repos = sorted({e['repository'] for e in entries})
    with ThreadPoolExecutor(jobs) as ex:
        loaded = dict(zip(repos, ex.map(lambda r: ensure_cache(r, cache, template), repos)))
    with ThreadPoolExecutor(jobs) as ex:
        recs = list(ex.map(lambda e: classify(e, *loaded[e['repository']]), entries))
    recs += [{'id': e['id'], 'repository': e['repository'], 'path': e['path'], 'pinnedCommit': e['commit'],
              'state': 'skipped', 'reason': 'temporarily unreadable: ' + skipped[e['repository']]} for e in held]
    recs.sort(key=lambda r: r['id'])
    if homes is not None:
        for r in recs:
            h = homes.get(r['id'])
            r['home'] = h
            r['homeMatches'] = None if h is None else (h == r['repository'])
    return recs


def summary(recs):
    out = ['state counts: ' + ', '.join(f"{s}={sum(r['state'] == s for r in recs)}" for s in STATES)]
    for s in STATES:
        c = Counter(r['reason'].split(' (')[0].split(':')[0] if s == 'unreachable' else r['reason'] for r in recs if r['state'] == s)
        for reason, n in c.most_common(6):
            out.append(f'  {s:11} {n:4}  {reason}')
    if any('homeMatches' in r for r in recs):
        known = [r for r in recs if r.get('homeMatches') is not None]
        out.append(f"home binding: {sum(r['homeMatches'] for r in known)} of {len(known)} agree "
                   f"with the registry; {sum(r.get('home') is None for r in recs)} entries have no binding")
    return '\n'.join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--root', default=str(ROOT))
    ap.add_argument('--cache')
    ap.add_argument('--shared-only', action='store_true',
                    help='only the offline shared-repository findings (ADR 0008); needs no cache or network')
    ap.add_argument('--findings-out')
    ap.add_argument('--homes')
    ap.add_argument('--out')
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--only-id')
    ap.add_argument('--url-template', default='git@github.com:{repo}.git')
    a = ap.parse_args(argv)
    entries = load_entries(a.root, a.only_id)
    findings = shared_findings(entries, load_declared(a.root))
    if a.findings_out:
        Path(a.findings_out).write_text(json.dumps(findings, indent=1, ensure_ascii=False) + '\n')
    if a.shared_only:
        print(findings_summary(findings))
        return 0
    if not a.cache:
        ap.error('--cache is required unless --shared-only')
    homes = json.loads(Path(a.homes).read_text()) if a.homes else None
    recs = run(entries, a.cache, a.url_template, a.jobs, homes)
    if a.out:
        Path(a.out).write_text(json.dumps(recs, indent=1, ensure_ascii=False) + '\n')
    print(summary(recs))
    print(findings_summary(findings))
    return 0


if __name__ == '__main__':
    sys.exit(main())
