import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from pack_profile import (build_car, car_read, cid_str, dag_cbor_decode,
                          dag_cbor_encode, unvarint, uvarint, verify_car,
                          CIDLink)


class TestVarint(unittest.TestCase):
    def test_roundtrip(self):
        for n in (0, 1, 127, 128, 300, 2**32, 2**64 - 1):
            v, off = unvarint(uvarint(n), 0)
            self.assertEqual((v, off), (n, len(uvarint(n))))


class TestDagCbor(unittest.TestCase):
    def test_roundtrip(self):
        doc = {'b': [1, -2, 'x', b'\x00\xff', None, True, False],
               'a': {'nested': CIDLink(b'\x01\x55\x12\x20' + b'\xab' * 32)}}
        raw = dag_cbor_encode(doc)
        back, end = dag_cbor_decode(raw, 0)
        self.assertEqual(end, len(raw))
        self.assertEqual(back['b'][:4], [1, -2, 'x', b'\x00\xff'])
        self.assertIsInstance(back['a']['nested'], CIDLink)


class TestCarBounded(unittest.TestCase):
    def test_pack_verify_roundtrip(self):
        files = [('SOUL.md', b'hello bot'), ('config.yaml', b'k: v\n'),
                 ('skills/a/SKILL.md', b'# skill\n' * 100)]
        car, pointer = build_car('test-bot', files)
        self.assertLessEqual(len(car), 1024 * 1024)
        self.assertTrue(pointer['cid'].startswith('b'))
        expected = {p: (hashlib.sha256(d).hexdigest(), len(d)) for p, d in files}
        got = verify_car(car, expected)
        self.assertEqual(got['files'], 3)
        self.assertEqual(got['cid'], pointer['cid'])

    def test_verify_refuses_tamper(self):
        files = [('SOUL.md', b'hello bot')]
        car, _ = build_car('test-bot', files)
        bad = bytearray(car)
        bad[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            verify_car(bytes(bad), {'SOUL.md': (hashlib.sha256(b'hello bot').hexdigest(), 9)})

    def test_verify_refuses_wrong_manifest(self):
        files = [('SOUL.md', b'hello bot')]
        car, _ = build_car('test-bot', files)
        with self.assertRaises(ValueError):
            verify_car(car, {'SOUL.md': ('0' * 64, 9)})

    def test_empty_refused(self):
        with self.assertRaises(ValueError):
            build_car('empty-bot', [])


if __name__ == '__main__':
    unittest.main()
