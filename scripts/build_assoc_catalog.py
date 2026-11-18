"""Project the pinned association rule data into the static Registry viewer."""

import hashlib
import json
import re
import shutil
from collections.abc import Mapping, Sequence
from datetime import date
from urllib.parse import urlsplit

import pycountry
from edn_format import Keyword, loads

DATASET_DIR = 'datasets/assoc'
RULES_PATH = 'data/datascript-tx.edn'
PAYLOAD_PATHS = {RULES_PATH, 'blueprint.edn', 'organization.edn', 'schema/association-rule.edn'}
RULE_FIELDS = {
    'id': 'id', 'title': 'title', 'url': 'url', 'url-provenance': 'provenance',
    'retrieved-at': 'retrievedAt', 'kind': 'kind', 'source-article': 'article',
    'established-date': 'establishedAt', 'last-revised-date': 'revisedAt',
    'corroborating-url': 'corroboratingUrl', 'corroborating-provenance': 'corroboratingProvenance',
}
REQUIRED_FIELDS = ('id', 'title', 'url', 'provenance', 'retrievedAt', 'kind')


def citation_url(value):
    parts = urlsplit(value)
    if (parts.scheme not in ('https', 'http') or not parts.hostname or parts.username
            or parts.password or re.search(r'[\s\\]', value)):
        raise ValueError(f'invalid citation URL: {value!r}')
    return value


def display_value(value):
    return value.name if isinstance(value, Keyword) else value


def read_rules(data, entry):
    source = loads(data.decode('utf-8'))
    # Most archives store a vector; EMF emits its sole record as a map.
    if isinstance(source, Mapping):
        source = [source]
    if not isinstance(source, Sequence) or isinstance(source, str):
        raise ValueError('expected an EDN map or vector of maps')

    rules = []
    seen = set()
    for row in source:
        if not isinstance(row, Mapping):
            raise ValueError('expected an association rule map')
        fields = {
            key.name.removeprefix('association-rule/'): value
            for key, value in row.items()
            if isinstance(key, Keyword) and key.name.startswith('association-rule/')
        }
        if any(fields.get(key) != entry['keys'][key] for key in ('country', 'isic')):
            raise ValueError('rule country or ISIC does not match its catalog entry')
        rule = {
            target: display_value(fields[key])
            for key, target in RULE_FIELDS.items() if fields.get(key) is not None
        }
        if any(not isinstance(value, str) for value in rule.values()):
            raise ValueError('expected string or keyword metadata')
        if any(not rule.get(field) for field in REQUIRED_FIELDS) or rule['id'] in seen:
            raise ValueError('missing required metadata or duplicate rule ID')
        for field in ('url', 'corroboratingUrl'):
            if field in rule:
                citation_url(rule[field])
        date.fromisoformat(rule['retrievedAt'])
        seen.add(rule['id'])
        rules.append(rule)
    return rules


def association(entry, dataset_dir, source_dir):
    repo, commit = entry['repository'], entry['commit']
    if not re.fullmatch(r'cloud-itonami/[\w.-]+', repo) or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError(f"{entry['id']}: invalid repository or commit")
    slug = entry['id'].removeprefix('assoc/')
    if not re.fullmatch(r'[0-9]{4}-[a-z]{2,3}-[a-z0-9-]+', slug) or entry['id'] != f'assoc/{slug}':
        raise ValueError(f"{entry['id']}: invalid association ID")
    country = entry['keys'].get('country')
    region = pycountry.countries.get(alpha_3=country) if country else None
    record = {
        'id': entry['id'],
        'name': entry.get('name', entry['id']),
        'country': country,
        'countryAlpha2': region.alpha_2 if region else country,
        'isic': entry['keys'].get('isic'),
        'repository': repo,
        'commit': commit,
        'license': entry['license'],
        'archived': entry['archived'],
        'rules': None,
    }
    if entry['digestStatus'] == 'verified':
        try:
            payload = {item['path']: item['sha256'] for item in entry['payload']}
            if set(payload) != PAYLOAD_PATHS:
                raise ValueError('unexpected payload paths')
            for path, digest in payload.items():
                data = (dataset_dir / slug / path).read_bytes()
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError(f'SHA-256 mismatch: {path}')
                if path == RULES_PATH:
                    rules_data = data
            record['rules'] = read_rules(rules_data, entry)
            record['rulesSha256'] = payload[RULES_PATH]
            record['sourcePath'] = f'source/{slug}/datascript-tx.edn'
            output = source_dir / slug / 'datascript-tx.edn'
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(rules_data)
        except (ValueError, OSError) as error:
            raise ValueError(f"{entry['id']} ({repo}@{commit}): could not bundle snapshot: {error}") from error
    return record


def build(root, out):
    catalog = json.loads((root / 'catalogs/datasets/assoc.json').read_text(encoding='utf-8'))
    dataset_dir, source_dir = root / DATASET_DIR, out / 'source'
    associations = [association(entry, dataset_dir, source_dir) for entry in catalog['entries']]
    source_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(dataset_dir / 'LICENSE.txt', source_dir / 'LICENSE.txt')
    data = json.dumps({'observedOn': catalog['observedOn'], 'associations': associations},
                      ensure_ascii=False, separators=(',', ':'))
    # The inert data block eliminates runtime requests and works from bundled local assets.
    page = (root / 'web/assoc/index.html').read_text(encoding='utf-8')
    (out / 'index.html').write_text(page.replace('<!-- ASSOC_DATA -->', data.replace('<', '\\u003c')),
                                    encoding='utf-8')
