import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_api_catalog import api_entry, family, host
from build_index import build, entries
from validate import validate


class ApiCatalogTests(unittest.TestCase):
    """ADR 0005: api entries are self-pinned shapes with honest status fields."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name) / 'registry'
        shutil.copytree(ROOT, cls.base, ignore=shutil.ignore_patterns('.git', '__pycache__', '.venv', 'site'))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp_case = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_case.cleanup)
        self.root = Path(self.temp_case.name) / 'registry'
        shutil.copytree(self.base, self.root)

    def mutate(self, path, change):
        p = self.root / path
        value = json.loads(p.read_text())
        change(value)
        p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

    def refused(self, path, change, pattern=None):
        self.mutate(path, change)
        build(self.root)
        if pattern:
            with self.assertRaisesRegex(Exception, pattern):
                validate(self.root)
        else:
            with self.assertRaises(Exception):
                validate(self.root)

    def test_circleci_is_a_shape_only_api_entry(self):
        m = json.loads((self.root / 'apis/com-circleci/manifest.json').read_text())
        self.assertEqual((m['api']['kind'], m['api']['tier']), ('compat', 'L5'))
        self.assertEqual(m['status']['execution'], 'none')
        self.assertFalse(m['status']['runtimeQualified'])
        self.assertFalse(m['status']['authority']['grants'])
        self.assertIn('vendorSource', m['api'])
        self.assertIn('api/com-circleci', {e['type'] + '/' + e['id'] for e in entries(self.root)})

    def test_cannot_claim_runtime_qualification(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['status'].update(runtimeQualified=True))

    def test_cannot_grant_authority(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['status']['authority'].update(grants=True))

    def test_cannot_claim_execution(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['status'].update(execution='browser-local'))

    def test_unpinned_source_refused(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m.update(source='https://github.com/kotoba-lang/com-circleci/tree/main'))

    def test_source_must_match_pin(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['pin'].update(commit='0' * 40), 'differs from its pin')

    def test_compat_pin_resolves_inside_this_registry(self):
        m = json.loads((self.root / 'apis/com-circleci/manifest.json').read_text())
        self.assertEqual((m['pin']['repository'], m['pin']['path']), ('cloud-itonami/app-itonami-itonami-registry', 'compat/com-circleci'))
        self.assertEqual(m['pin']['origin']['repository'], 'kotoba-lang/com-circleci')
        self.assertTrue(m['version'].startswith('1.0.0+' + m['pin']['origin']['commit'][:12]))

    def test_internalized_pin_needs_its_origin(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['pin'].pop('origin'), 'path and origin')

    def test_internalized_pin_must_match_classification(self):
        self.refused('catalogs/api-classification.json',
                     lambda d: [r.update(retiredTo=dict(r['retiredTo'], commit='0' * 40)) for r in d['entries'] if r['repository'] == 'kotoba-lang/com-circleci'],
                     'differs from its classification row')

    def test_conformance_claim_must_follow_source(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['status'].update(vendorConformance='not-claimed'), 'vendor conformance')

    def test_domain_requires_recorded_status(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['api']['origin'].update(domain='circleci.com'))

    def test_route_count_must_agree(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['api'].update(routeCount=1), 'route count')

    def test_copied_repository_file_refused(self):
        (self.root / 'apis/com-circleci/openapi.json').write_text('{}')
        build(self.root)
        with self.assertRaisesRegex(ValueError, 'must not copy'):
            validate(self.root)

    def test_classification_must_cover_every_entry(self):
        def change(d):
            row = next(r for r in d['entries'] if r.get('entry') == 'api/com-circleci')
            row.pop('entry')
            row.update({'class': 'unclassified', 'reason': 'no-api-manifest'})
        self.refused('catalogs/api-classification.json', change)

    def test_unclassified_needs_reason(self):
        def change(d):
            row = next(r for r in d['entries'] if r['class'] == 'unclassified')
            row.pop('reason')
        self.refused('catalogs/api-classification.json', change)

    def test_counts_must_agree(self):
        self.refused('catalogs/api-classification.json', lambda d: d['counts']['byClass'].update(api=1), 'count mismatch')

    def test_recorded_origin_comes_from_the_extract(self):
        m = json.loads((self.root / 'apis/com-stripe/manifest.json').read_text())
        self.assertEqual((m['api']['origin']['status'], m['api']['origin']['reverseDomain']), ('recorded', 'com.stripe'))
        self.assertTrue(m['version'].split('+')[1].startswith(m['pin'].get('origin', m['pin'])['commit'][:12] + '.x'))

    def test_origin_without_extract_fact_refused(self):
        def change(m):
            m['api']['origin'] = {'status': 'recorded', 'domain': 'circleci.com', 'reverseDomain': 'com.circleci',
                                  'record': 'catalogs/origin-domains.json', 'nameMatchesDomain': True}
        self.refused('apis/com-circleci/manifest.json', change, 'without a fact')

    def test_origin_must_match_extract(self):
        self.refused('catalogs/origin-domains.json',
                     lambda d: next(e for e in d['entries'] if e['api'] == 'com-stripe').update(domain='stripe.net', reverseDomain='net.stripe', nameMatchesDomain=False),
                     'differs from the extract')

    def test_reverse_domain_must_reverse_domain(self):
        self.refused('catalogs/origin-domains.json',
                     lambda d: next(e for e in d['entries'] if e['api'] == 'com-stripe').update(reverseDomain='com.stripe.api'),
                     'reversed domain')

    def test_extract_only_names_api_entries(self):
        def change(d):
            d['entries'].append({'api': 'org-ietf-x509', 'repository': 'kotoba-lang/org-ietf-x509', 'domain': 'ietf.org',
                                 'reverseDomain': 'org.ietf', 'nameMatchesDomain': True})
            d['count'] += 1
        self.refused('catalogs/origin-domains.json', change, 'no api entry')

    def test_relation_must_resolve(self):
        self.refused('apis/com-circleci/manifest.json', lambda m: m['relations'].update(implementedBy=['mcp/does-not-exist']), 'Unresolved API relation')

    def test_relation_overlay_must_be_reflected(self):
        self.refused('catalogs/api-relations.json',
                     lambda d: d['relations'].append({'api': 'com-circleci', 'implementedBy': ['mcp/mihari'], 'evidence': 'test'}),
                     'not reflected')


class GeneratorUnitTests(unittest.TestCase):
    def test_family(self):
        self.assertEqual(family('com-circleci'), 'com')
        self.assertEqual(family('cloud-filecoin'), 'cloud')
        self.assertEqual(family('gov.sec.edgar'), 'dot')
        self.assertIsNone(family('.github'))
        self.assertIsNone(family('kotoba'))

    def test_host_only_from_https_urls(self):
        self.assertEqual(host('https://circleci.com/api/v2/openapi.json'), 'circleci.com')
        self.assertIsNone(host('DrChrono official OpenAPI v4 (via apis.guru mirror: drchrono.com)'))

    def test_entry_never_derives_domain_from_name(self):
        manifest = {'kind': 'compat', 'tier': 'L4', 'title': 't', 'description': 'd', 'entities': ['A'],
                    'capabilities': {'api': {'type': 'rest', 'routes': [{'method': 'GET', 'path': '/v1/a', 'op': 'list A'}]}}}
        pin = {'commit': 'a' * 40, 'license': 'MIT', 'archived': False}
        e = api_entry('com-example', pin, manifest, [{'path': 'manifest.json', 'sha256': 'b' * 64, 'bytes': 1}], {})
        self.assertEqual(e['api']['origin'], {'status': 'unverified'})
        fact = {'domain': 'example.com', 'reverseDomain': 'com.example', 'nameMatchesDomain': True}
        e2 = api_entry('com-example', pin, manifest, [{'path': 'manifest.json', 'sha256': 'b' * 64, 'bytes': 1}], {}, {'com-example': fact})
        self.assertEqual(e2['api']['origin']['status'], 'recorded')
        self.assertNotEqual(e2['version'], e['version'])
        self.assertEqual(e['status']['vendorConformance'], 'not-claimed')


if __name__ == '__main__':
    unittest.main()
