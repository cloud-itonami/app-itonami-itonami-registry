import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_municipality_knowledge as build

SK = ROOT / 'skills/knowledge/municipal-ordinance-knowledge'


class OrdinanceCountTests(unittest.TestCase):
    def count(self, mid):
        return build.ordinance_count((SK / 'references/municipality' / mid / 'datascript-tx.edn').read_text())

    def test_key_order_does_not_change_the_count(self):
        # deu-munich sorts its keys and starts with :kind; it was counted as 0 while the file held 2.
        self.assertEqual(2, self.count('deu-munich'))
        self.assertEqual(2, self.count('deu-berlin'))       # starts with :id
        self.assertEqual(10, self.count('cze-prague'))      # starts with :citation-control
        self.assertEqual(13, self.count('pan-panama-city'))
        self.assertEqual(11, self.count('prt-lisbon'))

    def test_nested_braces_and_strings_are_not_records(self):
        text = ('[\n'
                '#:ordinance{:kind :ordinance, :topic #{:public-space :parks}, '
                ':title "Satzung {Fassung} #:ordinance{:id fake}", :id "a-1"}\n'
                '#:ordinance{:id "b-2", :title "t"}]\n')
        self.assertEqual(2, build.ordinance_count(text))

    def test_empty_catalog(self):
        self.assertEqual(0, build.ordinance_count('[]'))

    def test_index_counts_match_the_copied_archives(self):
        index = json.loads((SK / 'references/index.json').read_text())
        self.assertEqual(62, index['count'])
        for m in index['municipalities']:
            with self.subTest(municipality=m['id']):
                text = (SK / m['dir'] / 'datascript-tx.edn').read_text()
                self.assertEqual(build.ordinance_count(text), m['ordinances'])


class FromCopiesTests(unittest.TestCase):
    def test_digest_mismatch_stops_the_rebuild(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / 'references/municipality/x-city'
            folder.mkdir(parents=True)
            (folder / 'datascript-tx.edn').write_text('[]')
            entry = {'id': 'org/x-city',
                     'payload': [{'path': 'data/datascript-tx.edn', 'sha256': '0' * 64}]}
            original = build.SK
            build.SK = Path(d)
            try:
                with self.assertRaises(SystemExit):
                    build.local_copies([entry])
            finally:
                build.SK = original


if __name__ == '__main__':
    unittest.main()
