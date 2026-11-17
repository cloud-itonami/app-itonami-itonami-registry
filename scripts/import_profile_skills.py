#!/usr/bin/env python3
"""Import skills that live inside Itonami profile repositories into skills/<category>/<name>/ (ADR 0013).

For each skill name found under a profile's skills/ in the given repositories, the variant used by the
most repositories is the canonical one (ties: the lexicographically first repository). The skill folder
is copied from that repository's pinned default-branch commit; every copied file is recorded with its
sha256 in catalogs/sources.json, and an itonami.json sidecar is written. Nothing is executed.

    import_profile_skills.py --rows rows.json [--category-map NAME=CATEGORY ...]
rows.json: [[repo, path_of_SKILL.md, sha256, name, bytes], ...]
"""
import argparse, collections, hashlib, json, re, subprocess, sys, time, urllib.request
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
ORG = 'cloud-itonami'
MAX_FILE = 256 * 1024
CATEGORY = {
    'software-development': ['git-operations', 'git-cleanup-conflict', 'java-kotoba-migration', 'kbb-config-and-classpath',
                             'kbb-test-suite-fix', 'nbb-to-kbb-migration', 'isco4-kotoba-migration',
                             'kotoba-capability-extension', 'utsushi-jvmfree-bot', 'tenken-declarative-config'],
    'research': ['hyakka-knowledge-pipeline', 'hyakka-ontology-scout', 'hyakka-sitelink-scout',
                 'hyakka-source-scout', 'hyakka-wikidata-class-scout', 'yabai-intel-ioc-iteration'],
    'devops': ['hermes-fleet-cron-health', 'fleet-watchdog-ops', 'awai-state-store-policy', 'murakumo-edge-ring',
               'murakumo-confidential-inference', 'kotobase-bytes-plane', 'kotobase-ldbc-qualification',
               'mail-relay-inbox-observation', 'transport-evidence-bot'],
}
CAT = {n: c for c, ns in CATEGORY.items() for n in ns}


def sh(args):
    for t in range(5):
        p = subprocess.run(args, capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout
        time.sleep(2 + t)
    raise SystemExit(f'failed: {args[:4]} {p.stderr[:200]}')


def raw(repo, commit, path):
    url = f'https://raw.githubusercontent.com/{ORG}/{repo}/{commit}/{path}'
    for t in range(4):
        try:
            return urllib.request.urlopen(url, timeout=30).read()
        except Exception:
            time.sleep(1 + t)
    raise SystemExit(f'fetch failed: {url}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rows', required=True)
    ap.add_argument('--date', default='2026-11-17')
    a = ap.parse_args()
    rows = json.load(open(a.rows))
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    for repo, path, sha, name, _ in rows:
        if name:
            groups[name][sha].append((repo, path))
    sources = json.loads((ROOT / 'catalogs/sources.json').read_text())
    src_by_id = {s['id']: s for s in sources['sources']}
    commits, report = {}, []
    for name in sorted(groups):
        sha, owners = max(groups[name].items(), key=lambda kv: (len(kv[1]), [-ord(c) for c in sorted(kv[1])[0][0]]))
        repo, path = sorted(owners)[0]
        if repo not in commits:
            commits[repo] = sh(['gh', 'api', f'repos/{ORG}/{repo}/commits/HEAD', '--jq', '.sha']).strip()
        commit = commits[repo]
        folder = path.rsplit('/', 1)[0]
        tree = json.loads(sh(['gh', 'api', f'repos/{ORG}/{repo}/git/trees/{commit}?recursive=1']))['tree']
        files = [t for t in tree if t['type'] == 'blob' and t['mode'] in ('100644', '100755')
                 and t['path'].startswith(folder + '/') and t['size'] <= MAX_FILE]
        # a nested skill folder inside this folder is a separate skill; exclude it
        nested = {t['path'].rsplit('/', 1)[0] for t in files if t['path'].endswith('/SKILL.md') and t['path'] != path}
        files = [t for t in files if not any(t['path'].startswith(n + '/') for n in nested)]
        cat = CAT.get(name, 'operations')
        dest = ROOT / 'skills' / cat / name
        head = raw(repo, commit, path).decode('utf-8', 'replace')
        hp = head.split('---', 2)
        try:
            hm = yaml.safe_load(hp[1]) if head.startswith('---') and len(hp) == 3 else None
        except yaml.YAMLError:
            hm = None
        if not isinstance(hm, dict) or not hm.get('description'):
            print(f'SKIPPED (no frontmatter description): {name} {repo}/{path}', file=sys.stderr)
            continue
        if dest.exists():
            raise SystemExit(f'exists: {dest}')
        recs = []
        for t in files:
            body = raw(repo, commit, t['path'])
            rel = t['path'][len(folder) + 1:]
            recs.append({'path': t['path'], 'sha256': hashlib.sha256(body).hexdigest(),
                         'url': f'https://github.com/{ORG}/{repo}/blob/{commit}/{t["path"]}'})
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            if rel == 'SKILL.md':
                text = body.decode('utf-8')
                parts = text.split('---', 2)
                meta = yaml.safe_load(parts[1]) if text.startswith('---') and len(parts) == 3 else {}
                if not isinstance(meta, dict) or not meta.get('description'):
                    raise SystemExit(f'no frontmatter description: {repo}/{path}')
                meta['name'] = name
                md = meta.setdefault('metadata', {}) if isinstance(meta.get('metadata'), dict) or 'metadata' not in meta else {}
                h = md.setdefault('hermes', {})
                h.update({'version': '0.1.0', 'author': 'cloud-itonami',
                          'source': f'https://github.com/{ORG}/{repo}/tree/{commit}',
                          'compatibility': {'hermes': '*', 'desktop': '*'}})
                meta.setdefault('license', 'AGPL-3.0-or-later')
                fm = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, width=1000)
                out.write_text('---\n' + fm + '---' + parts[2] if len(parts) == 3 else '---\n' + fm + '---\n' + text)
            else:
                out.write_bytes(body)
        sid = f"skillimport-{re.sub(r'^app-itonami-', '', repo)}-{commit[:8]}"
        s = src_by_id.get(sid)
        if s is None:
            s = {'id': sid, 'repository': f'{ORG}/{repo}', 'commit': commit, 'files': []}
            sources['sources'].append(s)
            src_by_id[sid] = s
        have = {f['path'] for f in s['files']}
        s['files'] += [r for r in recs if r['path'] not in have]
        desc = yaml.safe_load((dest / 'SKILL.md').read_text().split('---', 2)[1])['description']
        side = {
            'schemaVersion': 'itonami.entry.v1',
            'sourceRefs': [sid],
            'useWhen': re.sub(r'\s+', ' ', str(desc)).strip(),
            'avoidWhen': 'Outside the task its description names, or without the caller authorizing the effects its steps describe.',
            'inputs': {'skill': 'SKILL.md and its bundled files, as written in the owning profile'},
            'outputs': {'guidance': 'procedure text for the calling agent; the registry runs nothing'},
            'effects': ['unreviewed'],
            'authority': {'grants': False, 'default': 'blocked', 'binding': 'caller authorization'},
            'validation': {'catalog': 'schema-checked',
                           'runtime': f'copied verbatim from {repo} on {a.date} (variant used by {len(owners)} of '
                                      f'{sum(len(v) for v in groups[name].values())} profile copies); effects not reviewed; '
                                      'not run from the registry install path',
                           'live': False},
            'compatibilityNote': 'Hermes skill shape. SKILL.md frontmatter gained metadata.hermes and license; '
                                 'body and bundled files are unchanged. License AGPL-3.0-or-later per owner decision 2026-11-17. '
                                 'Wildcard versions express no runtime compatibility.',
        }
        (dest / 'itonami.json').write_text(json.dumps(side, indent=2, ensure_ascii=False) + '\n')
        report.append((name, cat, repo, len(owners), sum(len(v) for v in groups[name].values()), len(groups[name]), len(recs)))
    (ROOT / 'catalogs/sources.json').write_text(json.dumps(sources, indent=2, ensure_ascii=False) + '\n')
    for r in report:
        print(*r)


if __name__ == '__main__':
    sys.exit(main())
