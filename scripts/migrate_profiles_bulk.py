#!/usr/bin/env python3
"""Bulk-migrate all registry profile substances to AwaiVol as bounded CARs.

For each profiles/<id>/manifest.json: materialise files from git objects at
the pinned commit (via git archive, never the working tree), refuse anything
that is not an allowed profile file or differs from the manifest pin, pack a
bounded CAR (pack_profile), write it to the AwaiVol destination, read it back
and verify against the manifest. Emits pointers.json and coverage.json.
Re-runs resume: profiles already recorded with the same sourceCommit are
skipped.

Writes NOTHING to owning repositories. Registry manifests are untouched;
this run only produces the pointer catalog input (cutover is separate).
"""
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from pack_profile import build_car, verify_car
from profile_tree import allowed


def git_archive_files(checkout, commit, subpath):
    out = subprocess.run(['git', '-C', str(checkout), 'archive', commit, '--', subpath],
                         check=True, capture_output=True).stdout
    files, excluded = [], []
    with tarfile.open(fileobj=io.BytesIO(out), mode='r') as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            full = m.name
            prefix = subpath + '/'
            if not full.startswith(prefix):
                continue
            rel = full[len(prefix):]
            if rel.startswith('.') and '/' not in rel:
                continue
            data = tf.extractfile(m).read()
            if not allowed(rel):
                # Same authority as registration: the manifest lists exactly
                # the packed set; non-definition files (e.g. secrets.edn)
                # are never packed. ADR 0003 keeps secrets out of every store.
                excluded.append(rel)
                continue
            files.append((rel, data))
    if not any(p == 'SOUL.md' for p, _ in files):
        raise ValueError('no SOUL.md; not a profile')
    return files, excluded


def commit_present(checkout, commit):
    r = subprocess.run(['git', '-C', str(checkout), 'cat-file', '-t', commit],
                       capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == 'commit'


def main():
    ap = __import__('argparse').ArgumentParser()
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--only', default='')
    ap.add_argument('--forest-root', default='/Users/junkawasaki/github')
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    only = set(filter(None, args.only.split(',')))

    pointers_path = out / 'pointers.json'
    coverage_path = out / 'coverage.json'
    prior = {}
    if pointers_path.exists():
        prior = {p['id']: p for p in json.loads(pointers_path.read_text())}

    manifests = sorted((ROOT / 'profiles').glob('*/manifest.json'))
    if only:
        manifests = [m for m in manifests if m.parent.name in only]
    if args.limit:
        manifests = manifests[:args.limit]

    pointers, skipped = [], []
    done = 0
    for mi, mpath in enumerate(manifests):
        pid = mpath.parent.name
        m = json.loads(mpath.read_text())
        prof = m['profile']
        repo, commit = prof['repository'], prof['commit']
        key = (pid, repo, commit)
        prev = prior.get(pid)
        if prev and (prev.get('repository'), prev.get('sourceCommit')) == (repo, commit):
            pointers.append(prev)
            done += 1
            continue
        checkout = Path(args.forest_root) / repo
        reason = None
        try:
            if not checkout.is_dir():
                raise RuntimeError(f'owning checkout missing: {repo}')
            if not commit_present(checkout, commit):
                raise RuntimeError(f'pinned commit absent locally: {commit[:12]}')
            files, excluded = git_archive_files(checkout, commit, prof['path'])
            exp = {f['path']: (f['sha256'], f['bytes']) for f in prof['files']}
            got = {p: (__import__('hashlib').sha256(d).hexdigest(), len(d)) for p, d in files}
            if got != exp:
                raise RuntimeError('substance differs from registry pin')
            if excluded:
                pass  # recorded in the pointer below; secrets never packed
            car, pointer = build_car(pid, files)
            tmp = out / (pointer['carSha256'] + '.car.tmp')
            final = out / (pointer['carSha256'] + '.car')
            tmp.write_bytes(car)
            os.replace(tmp, final)
            back = final.read_bytes()
            res = verify_car(back, exp)
            assert res['cid'] == pointer['cid']
            pointer.update({'repository': repo, 'sourceCommit': commit,
                            'carPath': str(final), 'excluded': sorted(excluded)})
            pointers.append(pointer)
            done += 1
        except Exception as e:  # record, never stop the bulk run
            skipped.append({'id': pid, 'repository': repo,
                            'commit': commit[:12], 'reason': f'{type(e).__name__}: {e}'})
        if (mi + 1) % 50 == 0:
            print(f'progress {mi + 1}/{len(manifests)} migrated={done} skipped={len(skipped)}',
                  flush=True)

    pointers.sort(key=lambda p: p['id'])
    pointers_path.write_text(json.dumps(pointers, indent=2) + '\n')
    coverage_path.write_text(json.dumps(
        {'migrated': len(pointers), 'skipped': skipped,
         'total': len(pointers) + len(skipped)}, indent=2) + '\n')
    print(f'DONE migrated={len(pointers)} skipped={len(skipped)}')


if __name__ == '__main__':
    main()
