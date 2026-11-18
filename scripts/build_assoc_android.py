#!/usr/bin/env python3
"""Wrap the normal static Registry build for the Tauri Android app."""

from html import escape
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

    dist = APP / 'dist'
    build(ROOT, dist)
    (dist / 'mobile-links.mjs').write_bytes((APP / 'mobile-links.mjs').read_bytes())
    home = dist / 'index.html'
    home_html = home.read_text(encoding='utf-8')
    home.write_text(home_html.replace('</body>', '<script type="module" src="./mobile-links.mjs"></script>\n</body>', 1),
                    encoding='utf-8')
    assoc = dist / 'assoc'
    for path in sorted(assoc.glob('source/*/datascript-tx.edn')):
        # Retain the original bytes, and use a static escaped text view on Android.
        content = escape(path.read_text(encoding='utf-8'))
        path.with_suffix('.edn.html').write_text(
            '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            """<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">"""
            '<title>検証済みの収録データ（EDN）</title>'
            '<style>body{color-scheme:light dark;margin:1rem}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'
            f'</head><body><h1>検証済みの収録データ（EDN）</h1><pre tabindex="0">{content}</pre></body></html>',
            encoding='utf-8',
        )
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
