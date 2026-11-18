#!/usr/bin/env python3
"""Wrap the normal static Registry build for the Tauri Android app."""

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from build_site import ROOT, build

APP = ROOT / 'android/assoc'
RUNTIME_COMMIT = '05fc7c5c62ca0e44fc9d7539fe9834ec9a6b0b14'
RUNTIME_PATH = 'lib/kotoba.wasmWebcomponent/src/kotoba-client-runtime.js'
RUNTIME_SHA256 = '5a950051c484a992caba0ad9edff780938648f9cade0b18f2d016812742ee6fb'
SCRIPT = '<script src="./assoc.js" defer></script>'


def pinned_source(path, expected_sha256):
    url = f'https://raw.githubusercontent.com/kotoba-lang/kotoba/{RUNTIME_COMMIT}/{path}'
    with urlopen(url, timeout=30) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError(f'Kotoba source SHA-256 mismatch: {path}')
    return data


def main():
    descriptor = json.loads((APP / 'client-runtime.json').read_text(encoding='utf-8'))
    broker = pinned_source(RUNTIME_PATH, RUNTIME_SHA256)
    license_bytes = pinned_source('LICENSE', 'c95bae1d1ce0235ecccd3560b772ec1efb97f348a79f0fbe0a634f0c2ccefe2c')
    notice_bytes = pinned_source('NOTICE', 'a263dafd3b98365765d784f139c44888ef6298d5b2b9ef6edbc5d84ffb86b0c9')

    build(ROOT, APP / 'dist')
    assoc = APP / 'dist/assoc'
    (assoc / 'kotoba-client-runtime.mjs').write_bytes(broker)
    (assoc / 'KOTOBA-LICENSE.txt').write_bytes(license_bytes)
    (assoc / 'KOTOBA-NOTICE.txt').write_bytes(notice_bytes)
    (assoc / 'bootstrap.mjs').write_bytes((APP / 'bootstrap.mjs').read_bytes())
    page = assoc / 'index.html'
    text = page.read_text(encoding='utf-8')
    if text.count(SCRIPT) != 1:
        raise ValueError('The Registry viewer script entry has changed')
    data = json.dumps(descriptor, ensure_ascii=True).replace('<', '\\u003c')
    wrapper = (
        f'<script id="assoc-client-runtime" type="application/json">{data}</script>\n'
        '<script type="module" src="./bootstrap.mjs"></script>'
    )
    page.write_text(text.replace(SCRIPT, wrapper, 1), encoding='utf-8')
    print(f'Bundled Registry viewer and verified Kotoba runtime {RUNTIME_COMMIT}')


if __name__ == '__main__':
    main()
