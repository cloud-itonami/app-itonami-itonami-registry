#!/usr/bin/env python3
"""Pack an Itonami profile substance folder into a bounded CARv2 file.

Bounded profile (per the Otehon storage contract): raw-codec 64KiB leaves,
one DAG-CBOR root, at most 64 leaves, CAR total at most 1MiB, no index.
Refuses anything outside that profile instead of widening it.

Reads profile files from git objects at a pinned commit (never the working
tree), verifies them against the registry manifest hashes, packs the canonical
payload, and emits a pointer record {cid, carSha256, carBytes, payloadSha256}.

A separate decode path (decode_dag_cbor / car_read) verifies CARs without
reusing the encoder, so `python scripts/pack_profile.py --verify` is an
independent readback of what is on AwaiVol.
"""
import argparse
import base64
import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEAF_SIZE = 64 * 1024
MAX_LEAVES = 64
MAX_CAR = 1024 * 1024
CODEC_RAW = 0x55
CODEC_DAG_CBOR = 0x71

# --- varint (LEB128 unsigned) ---

def uvarint(n):
    if n < 0:
        raise ValueError('negative varint')
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def unvarint(buf, off):
    n = shift = 0
    while True:
        if off >= len(buf):
            raise ValueError('truncated varint')
        b = buf[off]
        off += 1
        n |= (b & 0x7F) << shift
        if not b & 0x80:
            return n, off
        shift += 7
        if shift >= 64:
            raise ValueError('varint overflow')


# --- minimal DAG-CBOR encoder (deterministic: shortest ints, sorted maps) ---

def _head(major, n):
    if n < 24:
        return bytes([(major << 5) | n])
    if n < 256:
        return bytes([(major << 5) | 24, n])
    if n < 65536:
        return bytes([(major << 5) | 25]) + struct.pack('>H', n)
    if n < 2**32:
        return bytes([(major << 5) | 26]) + struct.pack('>I', n)
    if n < 2**64:
        return bytes([(major << 5) | 27]) + struct.pack('>Q', n)
    raise ValueError('int too large')


def dag_cbor_encode(v):
    if v is None:
        return b'\xf6'
    if isinstance(v, bool):
        return b'\xf5' if v else b'\xf4'
    if isinstance(v, int):
        if v >= 0:
            return _head(0, v)
        return _head(1, -1 - v)
    if isinstance(v, bytes):
        return _head(2, len(v)) + v
    if isinstance(v, str):
        b = v.encode('utf-8')
        return _head(3, len(b)) + b
    if isinstance(v, CIDLink):
        return _head(6, 42) + dag_cbor_encode(v.cid_bytes)
    if isinstance(v, list):
        return _head(4, len(v)) + b''.join(dag_cbor_encode(x) for x in v)
    if isinstance(v, dict):
        items = sorted(v.items(), key=lambda kv: (len(kv[0]), kv[0]))
        for k in v:
            if not isinstance(k, str):
                raise ValueError('map keys must be text')
        return _head(5, len(v)) + b''.join(
            dag_cbor_encode(k) + dag_cbor_encode(val) for k, val in items)
    raise ValueError(f'unsupported type {type(v)}')


class CIDLink:
    def __init__(self, cid_bytes):
        self.cid_bytes = cid_bytes


# --- independent DAG-CBOR decoder ---

def _read_arg(buf, off, ai):
    if ai < 24:
        return ai, off
    if ai == 24:
        return buf[off], off + 1
    if ai == 25:
        return struct.unpack('>H', buf[off:off + 2])[0], off + 2
    if ai == 26:
        return struct.unpack('>I', buf[off:off + 4])[0], off + 4
    if ai == 27:
        return struct.unpack('>Q', buf[off:off + 8])[0], off + 8
    raise ValueError('indefinite lengths refused')


def dag_cbor_decode(buf, off=0):
    if off >= len(buf):
        raise ValueError('truncated cbor')
    ib = buf[off]
    off += 1
    major, ai = ib >> 5, ib & 0x1F
    if major == 7:
        if ib == 0xF6:
            return None, off
        if ib == 0xF5:
            return True, off
        if ib == 0xF4:
            return False, off
        raise ValueError('floats/simple refused')
    if major == 0:
        n, off = _read_arg(buf, off, ai)
        return n, off
    if major == 1:
        n, off = _read_arg(buf, off, ai)
        return -1 - n, off
    if major in (2, 3):
        n, off = _read_arg(buf, off, ai)
        if off + n > len(buf):
            raise ValueError('truncated bytes/text')
        raw = buf[off:off + n]
        off += n
        if major == 2:
            return raw, off
        return raw.decode('utf-8'), off
    if major == 4:
        n, off = _read_arg(buf, off, ai)
        out = []
        for _ in range(n):
            v, off = dag_cbor_decode(buf, off)
            out.append(v)
        return out, off
    if major == 5:
        n, off = _read_arg(buf, off, ai)
        out = {}
        for _ in range(n):
            k, off = dag_cbor_decode(buf, off)
            v, off = dag_cbor_decode(buf, off)
            if not isinstance(k, str):
                raise ValueError('non-text map key')
            out[k] = v
        return out, off
    if major == 6:
        tag, off = _read_arg(buf, off, ai)
        v, off = dag_cbor_decode(buf, off)
        if tag == 42 and isinstance(v, bytes):
            return CIDLink(v), off
        raise ValueError(f'unsupported tag {tag}')
    raise ValueError('unsupported major type')


# --- CIDs ---

def cid_bytes(codec, digest):
    return b'\x01' + bytes([codec]) + b'\x12\x20' + digest


def cid_str(cid):
    return 'b' + base64.b32encode(cid).decode('ascii').lower().rstrip('=')


# --- canonical payload ---

def canonical_payload(files):
    """files: list of (path, data) sorted by path. Returns (payload, index)."""
    files = sorted(files, key=lambda f: f[0])
    payload = bytearray()
    index = []
    for path, data in files:
        pb = path.encode('utf-8')
        off = len(payload)
        payload += uvarint(len(pb)) + pb + uvarint(len(data)) + data
        index.append({'path': path, 'offset': off, 'size': len(data),
                      'sha256': hashlib.sha256(data).hexdigest()})
    return bytes(payload), index


# --- CARv2 writer ---

CARV2_MAGIC = bytes([0x0A, 0xA1, 0x75, 0x6E, 0x69, 0x74, 0x79, 0x2D, 0x63, 0x61, 0x72])


def build_car(profile_id, files):
    payload, index = canonical_payload(files)
    if not files:
        raise ValueError('empty profile refused')
    leaves = [payload[i:i + LEAF_SIZE] for i in range(0, len(payload), LEAF_SIZE)]
    if len(leaves) > MAX_LEAVES:
        raise ValueError(f'{len(leaves)} leaves exceed {MAX_LEAVES}')
    leaf_cids = [cid_bytes(CODEC_RAW, hashlib.sha256(l).digest()) for l in leaves]
    root_doc = {
        'profile': profile_id,
        'payload-bytes': len(payload),
        'payload-sha256': hashlib.sha256(payload).digest(),
        'leaves': [CIDLink(c) for c in leaf_cids],
        'files': [{'path': e['path'], 'offset': e['offset'], 'size': e['size'],
                   'sha256': bytes.fromhex(e['sha256'])} for e in index],
    }
    root_data = dag_cbor_encode(root_doc)
    root_cid = cid_bytes(CODEC_DAG_CBOR, hashlib.sha256(root_data).digest())
    header = dag_cbor_encode({'version': 1, 'roots': [CIDLink(root_cid)]})
    blocks = [(root_cid, root_data)] + list(zip(leaf_cids, leaves))
    carv1 = uvarint(len(header)) + header
    for cid, data in blocks:
        carv1 += uvarint(len(cid) + len(data)) + cid + data
    # characteristics(16) + data_offset(8) + data_size(8) + index_offset(8, zero: no index)
    header40 = struct.pack('<QQ', 0, 0) + struct.pack('<Q', 51) + struct.pack('<Q', len(carv1)) + struct.pack('<Q', 0)
    assert len(header40) == 40
    car = CARV2_MAGIC + header40 + carv1
    if len(car) > MAX_CAR:
        raise ValueError(f'CAR {len(car)} bytes exceeds {MAX_CAR}')
    return car, {
        'id': profile_id,
        'cid': cid_str(root_cid),
        'carSha256': hashlib.sha256(car).hexdigest(),
        'carBytes': len(car),
        'payloadSha256': hashlib.sha256(payload).hexdigest(),
        'payloadBytes': len(payload),
        'leaves': len(leaves),
        'files': index,
    }


# --- independent CAR reader / verifier ---

def car_read(car):
    if car[:11] != CARV2_MAGIC:
        raise ValueError('not a CARv2 file')
    _c1, _c2, data_off, data_size, idx_off = struct.unpack('<QQQQQ', car[11:51])
    if (_c1, _c2) != (0, 0):
        raise ValueError('characteristics must be zero')
    if data_off != 51:
        raise ValueError('unexpected data offset')
    if idx_off != 0:
        raise ValueError('indexed CARs refused by this profile')
    if data_off + data_size != len(car):
        raise ValueError('trailing bytes or size mismatch')
    body = car[data_off:data_off + data_size]
    hlen, hstart = unvarint(body, 0)
    header, off = dag_cbor_decode(body, hstart)
    if off - hstart != hlen:
        raise ValueError('header length mismatch')
    if header.get('version') != 1 or len(header.get('roots', [])) != 1:
        raise ValueError('exactly one root required')
    root_link = header['roots'][0]
    if not isinstance(root_link, CIDLink):
        raise ValueError('root must be a CID link')
    blocks = {}
    while off < len(body):
        blen, off = unvarint(body, off)
        end = off + blen
        if end > len(body):
            raise ValueError('truncated block')
        blk = body[off:end]
        off = end
        # split CID prefix: 0x01 <codec:varint> 0x12 0x20 <32 bytes>
        if len(blk) < 36 or blk[0] != 0x01 or blk[2:4] != b'\x12\x20':
            raise ValueError('non sha2-256 CIDv1 block refused')
        codec = blk[1]
        digest, data = blk[4:36], blk[36:]
        if hashlib.sha256(data).digest() != digest:
            raise ValueError('block digest mismatch')
        if codec == CODEC_RAW and len(data) > LEAF_SIZE:
            raise ValueError('oversize raw leaf')
        if codec not in (CODEC_RAW, CODEC_DAG_CBOR):
            raise ValueError('unknown codec')
        blocks[bytes(blk[:36])] = (codec, data)
    return root_link.cid_bytes, blocks


def verify_car(car, expected_files):
    """expected_files: {path: (sha256hex, size)}. Rebuilds payload from CAR."""
    root_cid, blocks = car_read(car)
    if root_cid[1] != CODEC_DAG_CBOR:
        raise ValueError('root must be dag-cbor')
    _codec, root_data = blocks[root_cid]
    if hashlib.sha256(root_data).digest() != root_cid[4:36]:
        raise ValueError('root digest mismatch')
    doc, end = dag_cbor_decode(root_data, 0)
    if end != len(root_data):
        raise ValueError('trailing bytes in root document')
    leaf_datas = []
    for link in doc['leaves']:
        if not isinstance(link, CIDLink):
            raise ValueError('leaf must be a CID link')
        codec, data = blocks[link.cid_bytes]
        if codec != CODEC_RAW:
            raise ValueError('leaf must be raw codec')
        leaf_datas.append(data)
    payload = b''.join(leaf_datas)
    if hashlib.sha256(payload).digest() != doc['payload-sha256']:
        raise ValueError('payload digest mismatch')
    if len(payload) != doc['payload-bytes']:
        raise ValueError('payload size mismatch')
    got = {}
    for fe in doc['files']:
        path = fe['path']
        # frame: varint(pathlen) path varint(datalen) data at offset
        p = fe['offset']
        plen, p = unvarint(payload, p)
        name = payload[p:p + plen].decode('utf-8')
        p += plen
        if name != path:
            raise ValueError(f'path mismatch at offset: {name} != {path}')
        dlen, p = unvarint(payload, p)
        data = payload[p:p + dlen]
        if len(data) != dlen or len(data) != fe['size']:
            raise ValueError(f'size mismatch: {path}')
        if hashlib.sha256(data).digest() != fe['sha256']:
            raise ValueError(f'content mismatch: {path}')
        got[path] = (hashlib.sha256(data).hexdigest(), len(data))
    if set(got) != set(expected_files):
        raise ValueError('file set differs from manifest')
    for path, (h, s) in expected_files.items():
        if got[path] != (h, s):
            raise ValueError(f'manifest mismatch: {path}')
    return {'cid': cid_str(root_cid), 'files': len(got),
            'payloadBytes': len(payload)}


# --- git source ---

def git_files(checkout, commit, subpath):
    out = subprocess.run(['git', '-C', str(checkout), 'ls-tree', '-r', '-z',
                          '--name-only', commit, '--', subpath],
                         check=True, capture_output=True).stdout.decode().split('\0')
    files = []
    for name in filter(None, out):
        rel = name[len(subpath) + 1:]
        if rel.startswith('.') and '/' not in rel:
            continue
        data = subprocess.run(['git', '-C', str(checkout), 'show', f'{commit}:{name}'],
                              check=True, capture_output=True).stdout
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.profile_tree import allowed
        if not allowed(rel):
            # Registration authority: the manifest lists the packed set.
            # Non-definition files (e.g. secrets.edn) are never packed.
            print(f'excluded non-definition file: {rel}', file=sys.stderr)
            continue
        files.append((rel, data))
    if not any(p == 'SOUL.md' for p, _ in files):
        raise SystemExit(f'{subpath} has no SOUL.md; not a profile')
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkout')
    ap.add_argument('--commit')
    ap.add_argument('--path')
    ap.add_argument('--id')
    ap.add_argument('--out-dir', help='AwaiVol destination directory')
    ap.add_argument('--verify', help='verify this CAR file instead of packing')
    ap.add_argument('--expect', help='manifest.json to verify against with --verify')
    args = ap.parse_args()

    if args.verify:
        if args.expect is None:
            raise SystemExit('--verify needs --expect manifest.json')
        car = Path(args.verify).read_bytes()
        expected = {}
        if args.expect:
            m = json.loads(Path(args.expect).read_text())
            expected = {f['path']: (f['sha256'], f['bytes']) for f in m['profile']['files']}
        result = verify_car(car, expected)
        print(json.dumps(result, indent=2))
        return

    for flag in ('checkout', 'commit', 'path', 'id', 'out_dir'):
        if getattr(args, flag) is None:
            raise SystemExit(f'packing needs --{flag.replace("_", "-")}')
    files = git_files(args.checkout, args.commit, args.path)
    mpath = ROOT / 'profiles' / args.id / 'manifest.json'
    if mpath.exists():
        m = json.loads(mpath.read_text())
        exp = {f['path']: (f['sha256'], f['bytes']) for f in m['profile']['files']}
        got = {p: (hashlib.sha256(d).hexdigest(), len(d)) for p, d in files}
        if got != exp:
            raise SystemExit('substance differs from registry pin; refusing to pack')
    car, pointer = build_car(args.id, files)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / (pointer['carSha256'] + '.car.tmp')
    final = out / (pointer['carSha256'] + '.car')
    tmp.write_bytes(car)
    os.replace(tmp, final)
    pointer['carPath'] = str(final)
    print(json.dumps(pointer, indent=2))


if __name__ == '__main__':
    main()
