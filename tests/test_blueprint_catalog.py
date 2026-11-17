import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate import validate_blueprints


class BlueprintCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'catalogs').mkdir()
        (self.root / 'schemas').mkdir()
        shutil.copy(ROOT / 'catalogs/blueprints.json', self.root / 'catalogs')
        shutil.copy(ROOT / 'schemas/blueprint-sources.schema.json', self.root / 'schemas')

    def refused(self, change):
        p = self.root / 'catalogs/blueprints.json'
        doc = json.loads(p.read_text())
        change(doc)
        p.write_text(json.dumps(doc))
        with self.assertRaises(Exception):
            validate_blueprints(self.root)

    def test_published_catalog(self):
        validate_blueprints(self.root)

    def test_unpinned_commit_refused(self):
        self.refused(lambda d: d['entries'][0].update(commit='main'))

    def test_nonpublic_refused(self):
        self.refused(lambda d: d['entries'][0].update(visibility='private'))

    def test_grant_refused(self):
        self.refused(lambda d: d['entries'][0]['authority'].update(grants=True))

    def test_count_must_agree(self):
        self.refused(lambda d: d.update(count=d['count'] + 1))

    def test_duplicate_repository_refused(self):
        def dup(d):
            d['entries'][1]['repository'] = d['entries'][0]['repository']
        self.refused(dup)

    def test_blueprint_file_required(self):
        def drop(d):
            e = d['entries'][0]
            e['payload'] = [p for p in e['payload'] if p['path'] != 'blueprint.edn']
        self.refused(drop)

    def test_unknown_payload_path_refused(self):
        self.refused(lambda d: d['entries'][0]['payload'].append({'path': 'state.db', 'sha256': '0' * 64}))


if __name__ == '__main__':
    unittest.main()
