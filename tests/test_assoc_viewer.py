import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from build_assoc_catalog import RULES_PATH, association, build

RULE = b'''#:association-rule{:id "r1" :title "A </script> rule"
  :isic "0126" :country "MYS" :kind :membership-rule
  :url "https://example.org/rule" :url-provenance :official
  :retrieved-at "2026-10-25" :source-article "Section 2"}'''


def entry(data):
    return {
        'id': 'assoc/0126-mys-example', 'name': 'Example', 'keys': {'country': 'MYS', 'isic': '0126'},
        'repository': 'cloud-itonami/app-itonami-cloud-itonami-assoc-0126-mys-example',
        'commit': 'a' * 40, 'license': 'AGPL-3.0', 'archived': True,
        'digestStatus': 'verified',
        'payload': [{'path': RULES_PATH, 'sha256': hashlib.sha256(data).hexdigest()}],
    }


class AssocViewerTests(unittest.TestCase):
    def test_pinned_map_and_vector_keep_citations(self):
        for data in (RULE, b'[' + RULE + b']'):
            with self.subTest(data=data):
                source = entry(data)
                fetch = Mock(return_value=data)
                record = association(source, fetch)
                fetch.assert_called_once_with(
                    f"https://raw.githubusercontent.com/{source['repository']}/{source['commit']}/{RULES_PATH}")
                self.assertEqual(record['countryAlpha2'], 'MY')
                self.assertEqual(record['isic'], '0126')
                self.assertEqual(record['rules'][0], {
                    'id': 'r1', 'title': 'A </script> rule', 'url': 'https://example.org/rule',
                    'provenance': 'official', 'retrievedAt': '2026-10-25',
                    'kind': 'membership-rule', 'article': 'Section 2',
                })

    def test_mismatch_stops_the_build(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            association(entry(RULE), lambda url: RULE + b' ')

    def test_non_web_source_url_is_refused(self):
        data = RULE.replace(b'https://example.org/rule', b'javascript:void(0)')
        with self.assertRaisesRegex(ValueError, 'invalid citation URL'):
            association(entry(data), lambda url: data)

    def test_unverified_catalog_entry_does_not_fetch_rules(self):
        source = entry(RULE)
        source.update(digestStatus='unverified', keys={}, payload=[])
        fetch = Mock()
        self.assertIsNone(association(source, fetch)['rules'])
        fetch.assert_not_called()

    def test_generated_data_is_inert_inside_the_html(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'catalogs/datasets').mkdir(parents=True)
            (root / 'catalogs/datasets/assoc.json').write_text(json.dumps(
                {'observedOn': '2026-10-25', 'entries': [entry(RULE)]}))
            (root / 'web/assoc').mkdir(parents=True)
            (root / 'web/assoc/index.html').write_text('<script type="application/json"><!-- ASSOC_DATA --></script>')
            build(root, root, lambda url: RULE)
            page = (root / 'index.html').read_text()
            self.assertEqual(page.count('</script>'), 1)
            self.assertEqual(json.loads(page.split('>', 1)[1].removesuffix('</script>'))
                             ['associations'][0]['rules'][0]['title'], 'A </script> rule')
