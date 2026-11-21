"""Temporary source skip list (catalogs/skip-sources.json).

A listed repository is treated as temporarily unreadable: build, readback and re-pack
scripts do not fetch it and keep its existing registry entries unchanged. Nothing is
deleted, so removing the entry from the list makes the next run read it again.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_FILE = 'catalogs/skip-sources.json'


def load(root=ROOT):
    """Return {repository: reason} for every listed repository (empty if no list)."""
    path = Path(root) / SKIP_FILE
    if not path.exists():
        return {}
    doc = json.loads(path.read_text())
    out = {}
    for e in doc['entries']:
        if e['repository'] in out:
            raise ValueError(f"Duplicate skip-sources entry: {e['repository']}")
        out[e['repository']] = e['reason']
    return out


def note(repository, reason, what='read'):
    return f'skipped {what} (temporarily unreadable, {SKIP_FILE}): {repository}: {reason}'
