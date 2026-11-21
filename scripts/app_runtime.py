"""App client runtime per repository (catalogs/app-runtime.json, KOTOBA-159).

Registry entries (catalogs/blueprints.json, catalogs/profile-pointers.json) carry
`runtime` and `handlesUserDataOrExternalComms` copied from this catalog. A repository
with no record is `unknown` for both.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILE = 'catalogs/app-runtime.json'
UNKNOWN = {'runtime': 'unknown', 'handlesUserDataOrExternalComms': 'unknown'}


def load(root=ROOT):
    path = Path(root) / RUNTIME_FILE
    if not path.exists():
        return {'repositories': {}, 'trustedPageV1Baseline': {'repositories': []}}
    return json.loads(path.read_text())


def fields(doc, repository):
    """The two fields an entry for `repository` must carry."""
    rec = doc['repositories'].get(repository)
    if rec is None:
        return dict(UNKNOWN)
    return {'runtime': rec['runtime'], 'handlesUserDataOrExternalComms': rec['handlesUserDataOrExternalComms']}
