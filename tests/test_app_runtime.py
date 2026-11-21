import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import app_runtime  # noqa: E402
from validate import validate_app_runtime  # noqa: E402


class AppRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in ['catalogs/app-runtime.json', 'catalogs/blueprints.json', 'catalogs/profile-pointers.json',
                    'schemas/app-runtime.schema.json']:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.root / rel)

    def edit(self, rel, change):
        p = self.root / rel
        doc = json.loads(p.read_text())
        change(doc)
        p.write_text(json.dumps(doc))

    def test_published_catalog(self):
        validate_app_runtime(self.root)

    def test_new_trusted_page_refused(self):
        self.edit('catalogs/app-runtime.json', lambda d: d['repositories'].update(
            {'cloud-itonami/app-itonami-new': {'runtime': 'trusted-page-v1', 'handlesUserDataOrExternalComms': 'unknown',
                                               'basis': 'not-determined'}}))
        with self.assertRaises(ValueError):
            validate_app_runtime(self.root)

    def test_entry_must_carry_fields(self):
        def drop(d):
            del d['entries'][0]['runtime']
        self.edit('catalogs/blueprints.json', drop)
        with self.assertRaises(ValueError):
            validate_app_runtime(self.root)

    def test_entry_must_match_record(self):
        def flip(d):
            e = next(e for e in d['profiles'] if e['runtime'] == 'trusted-page-v1')
            e['runtime'] = 'restricted-wasm-v1'
        self.edit('catalogs/profile-pointers.json', flip)
        with self.assertRaises(ValueError):
            validate_app_runtime(self.root)

    def test_unrecorded_repository_is_unknown(self):
        self.assertEqual(app_runtime.fields({'repositories': {}}, 'x/y'), app_runtime.UNKNOWN)

    def test_trial_registrations_add_no_trusted_page(self):
        doc = app_runtime.load(ROOT)
        trial = [r for r, v in doc['repositories'].items() if v['basis'] == 'jun-1439-trial-review']
        self.assertEqual(len(trial), 20)
        self.assertTrue(all(doc['repositories'][r]['runtime'] == 'none' for r in trial))


if __name__ == '__main__':
    unittest.main()
