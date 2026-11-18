import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from build_assoc_catalog import DATASET_DIR, PAYLOAD_PATHS, RULES_PATH, association, build

RULE = b'''#:association-rule{:id "r1" :title "A </script> rule"
  :isic "0126" :country "MYS" :kind :membership-rule
  :url "https://example.org/rule" :url-provenance :official
  :retrieved-at "2026-10-25" :source-article "Section 2"}'''
SLUG = '0126-mys-example'


class AssocViewerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.dataset = self.root / DATASET_DIR
        self.source = self.root / 'out/source'

    def write_entry(self, data=RULE):
        payload = []
        for path in sorted(PAYLOAD_PATHS):
            contents = data if path == RULES_PATH else b'{}'
            dest = self.dataset / SLUG / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(contents)
            payload.append({'path': path, 'sha256': hashlib.sha256(contents).hexdigest()})
        return {
            'id': f'assoc/{SLUG}', 'name': 'Example', 'keys': {'country': 'MYS', 'isic': '0126'},
            'repository': f'cloud-itonami/app-itonami-cloud-itonami-assoc-{SLUG}',
            'commit': 'a' * 40, 'license': 'AGPL-3.0', 'archived': True,
            'digestStatus': 'verified', 'payload': payload,
        }

    def test_pinned_map_and_vector_keep_citations(self):
        for data in (RULE, b'[' + RULE + b']'):
            with self.subTest(data=data):
                record = association(self.write_entry(data), self.dataset, self.source)
                self.assertEqual(record['countryAlpha2'], 'MY')
                self.assertEqual(record['isic'], '0126')
                self.assertEqual(record['rules'][0], {
                    'id': 'r1', 'title': 'A </script> rule', 'url': 'https://example.org/rule',
                    'provenance': 'official', 'retrievedAt': '2026-10-25',
                    'kind': 'membership-rule', 'article': 'Section 2',
                })
                self.assertEqual(record['sourcePath'], f'source/{SLUG}/datascript-tx.edn')
                self.assertEqual((self.source.parent / record['sourcePath']).read_bytes(), data)

    def test_mismatch_stops_the_build(self):
        entry = self.write_entry()
        (self.dataset / SLUG / 'organization.edn').write_bytes(b'{:changed true}')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch: organization.edn'):
            association(entry, self.dataset, self.source)

    def test_missing_payload_stops_the_build(self):
        entry = self.write_entry()
        (self.dataset / SLUG / RULES_PATH).unlink()
        with self.assertRaisesRegex(ValueError, 'could not bundle snapshot'):
            association(entry, self.dataset, self.source)

    def test_non_web_source_url_is_refused(self):
        data = RULE.replace(b'https://example.org/rule', b'javascript:void(0)')
        with self.assertRaisesRegex(ValueError, 'invalid citation URL'):
            association(self.write_entry(data), self.dataset, self.source)

    def test_unverified_catalog_entry_does_not_read_rules(self):
        entry = self.write_entry()
        entry.update(digestStatus='unverified', keys={}, payload=[])
        self.assertIsNone(association(entry, self.root / 'missing', self.source)['rules'])
        self.assertFalse(self.source.exists())

    def test_generated_data_is_inert_inside_the_html(self):
        entry = self.write_entry()
        (self.root / 'catalogs/datasets').mkdir(parents=True)
        (self.root / 'catalogs/datasets/assoc.json').write_text(json.dumps(
            {'observedOn': '2026-10-25', 'entries': [entry]}))
        (self.root / 'web/assoc').mkdir(parents=True)
        (self.root / 'web/assoc/index.html').write_text('<script type="application/json"><!-- ASSOC_DATA --></script>')
        (self.dataset / 'LICENSE.txt').write_text('License')
        (self.source.parent).mkdir()
        build(self.root, self.source.parent)
        page = (self.source.parent / 'index.html').read_text()
        self.assertEqual(page.count('</script>'), 1)
        self.assertEqual(json.loads(page.split('>', 1)[1].removesuffix('</script>'))
                         ['associations'][0]['rules'][0]['title'], 'A </script> rule')
        self.assertEqual((self.source / 'LICENSE.txt').read_text(), 'License')
