import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate import validate_absorbed


class SubstanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'absorbed', self.root / 'absorbed')

    def test_absorbed_published(self):
        validate_absorbed(self.root)

    def test_modified_file_refused(self):
        target = next(p for p in (self.root / 'absorbed').rglob('*') if p.is_file() and p.name != 'ABSORBED.json')
        target.write_text(target.read_text() + 'x')
        with self.assertRaises(Exception):
            validate_absorbed(self.root)

    def test_extra_file_refused(self):
        folder = next((self.root / 'absorbed').iterdir())
        (folder / 'extra.txt').write_text('x')
        with self.assertRaises(Exception):
            validate_absorbed(self.root)


if __name__ == '__main__':
    unittest.main()
