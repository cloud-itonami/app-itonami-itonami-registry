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


class ClassificationKeyTests(unittest.TestCase):
    def test_versioned_keys_are_read(self):
        from build_blueprint_catalog import BP_CODE, CLASSIFICATION_KEYS
        for scheme, field in [('isic-rev4', 'isic'), ('isic-rev5', 'isic'), ('isco-08', 'isco'), ('cofog', 'cofog')]:
            found = BP_CODE.findall(f':itonami.blueprint/{scheme} "5820"')
            self.assertEqual(found, [(scheme, '5820')])
            self.assertEqual(CLASSIFICATION_KEYS[scheme], field)

    def test_unversioned_or_unknown_key_ignored(self):
        from build_blueprint_catalog import BP_CODE
        self.assertEqual(BP_CODE.findall(':itonami.blueprint/isic "5820" :itonami.blueprint/jsic-rev14 "391"'), [])

    def test_schema_lists_the_builder_keys(self):
        from build_blueprint_catalog import CLASSIFICATION_KEYS
        schema = json.loads((ROOT / 'schemas/blueprint-sources.schema.json').read_text())
        enum = schema['properties']['entries']['items']['properties']['keys']['properties']['classification']['enum']
        self.assertEqual(sorted(enum), sorted(CLASSIFICATION_KEYS))
