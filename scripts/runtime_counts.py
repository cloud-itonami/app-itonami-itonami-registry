#!/usr/bin/env python3
"""Count registry app entries by client runtime (KOTOBA-159), and how many
trusted-page-v1 apps handle user data or external communication."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import app_runtime  # noqa: E402


def counts(root=ROOT):
    doc = app_runtime.load(root)
    recs = doc['repositories']
    out = {'repositories': len(recs),
           'byRuntime': dict(Counter(r['runtime'] for r in recs.values()).most_common()),
           'trustedPageV1ByHandles': dict(Counter(str(r['handlesUserDataOrExternalComms']).lower()
                                                  for r in recs.values() if r['runtime'] == 'trusted-page-v1')),
           'unknownRuntime': sorted(k for k, r in recs.items() if r['runtime'] == 'unknown')}
    for name, path, key in [('blueprintEntries', 'catalogs/blueprints.json', 'entries'),
                            ('pointerEntries', 'catalogs/profile-pointers.json', 'profiles')]:
        rows = json.loads((Path(root) / path).read_text())[key]
        out[name] = dict(Counter(r.get('runtime') for r in rows).most_common())
    return out


if __name__ == '__main__':
    c = counts()
    if '--list-unknown' not in sys.argv:
        c['unknownRuntime'] = len(c['unknownRuntime'])
    print(json.dumps(c, indent=2, ensure_ascii=False))
