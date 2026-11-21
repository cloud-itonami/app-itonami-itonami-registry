import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import profile_status  # noqa: E402
import skip_sources  # noqa: E402
from validate import validate_skip_sources  # noqa: E402

ISCO = 'cloud-itonami/app-itonami-isco'


class SkipSourcesTests(unittest.TestCase):
    def test_published_list(self):
        skipped = skip_sources.load(ROOT)
        self.assertIn(ISCO, skipped)
        self.assertIn('AWAI-3629', skipped[ISCO])
        validate_skip_sources(ROOT)

    def test_skipped_entries_are_kept(self):
        pointers = json.loads((ROOT / 'catalogs/profile-pointers.json').read_text())['profiles']
        self.assertEqual(sum(p.get('repository') == ISCO for p in pointers), 8)

    def test_org_unspsc_listed_and_kept(self):
        repo = 'cloud-itonami/app-itonami-org-unspsc'
        self.assertIn('UNDP', skip_sources.load(ROOT)[repo])
        apps = json.loads((ROOT / 'catalogs/apps.json').read_text())['entries']
        self.assertTrue(any(e['repository'] == repo for e in apps))

    def test_un_classifications_listed_and_kept(self):
        apps = {e['repository'] for e in json.loads((ROOT / 'catalogs/apps.json').read_text())['entries']}
        for repo in ['cloud-itonami/app-itonami-org-un-isic', 'cloud-itonami/app-itonami-org-un-cofog']:
            self.assertIn('国連の許諾待ち', skip_sources.load(ROOT)[repo])
            self.assertIn(repo, apps)

    def test_profile_status_does_not_fetch_skipped(self):
        entries = [{'id': 'x', 'repository': ISCO, 'commit': '0' * 40, 'path': 'hermes/profiles/x',
                    'checksum': 'sha256-tree:' + '0' * 64}]
        recs = profile_status.run(entries, '/nonexistent-cache', 'https://invalid.example/{repo}', 1,
                                  skipped={ISCO: 'pending'})
        self.assertEqual([(r['id'], r['state']) for r in recs], [('x', 'skipped')])

    def test_removing_the_entry_restores_reading(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(skip_sources.load(Path(d)), {})

    def test_unreferenced_skip_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'catalogs').mkdir()
            (root / 'schemas').mkdir()
            (root / 'schemas/skip-sources.schema.json').write_text((ROOT / 'schemas/skip-sources.schema.json').read_text())
            doc = json.loads((ROOT / 'catalogs/skip-sources.json').read_text())
            (root / 'catalogs/skip-sources.json').write_text(json.dumps(doc))
            with self.assertRaises(ValueError):
                validate_skip_sources(root)


if __name__ == '__main__':
    unittest.main()
