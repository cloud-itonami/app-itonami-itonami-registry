import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import app_runtime  # noqa: E402
from validate import validate_app_runtime  # noqa: E402


class AppRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in ['catalogs/app-runtime.json', 'catalogs/blueprints.json', 'catalogs/profile-pointers.json',
                    'schemas/app-runtime.schema.json']:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.root / rel)

    def edit(self, rel, change):
        p = self.root / rel
        doc = json.loads(p.read_text())
        change(doc)
        p.write_text(json.dumps(doc))

    def test_published_catalog(self):
        validate_app_runtime(self.root)

    def test_new_trusted_page_entry_refused(self):
        repo = 'network-awai/app-yotei'  # recorded trusted-page-v1, not in the baseline
        self.edit('catalogs/app-runtime.json', lambda d: self.assertNotIn(repo, d['trustedPageV1Baseline']['repositories']))
        def add(d):
            e = dict(d['entries'][0], id='blueprint/network-awai/app-yotei', repository=repo,
                     runtime='trusted-page-v1', handlesUserDataOrExternalComms='unknown')
            d['entries'].append(e)
            d['count'] += 1
        self.edit('catalogs/blueprints.json', add)
        with self.assertRaises(ValueError):
            validate_app_runtime(self.root)

    def test_trusted_page_may_be_counted(self):
        doc = json.loads((self.root / 'catalogs/app-runtime.json').read_text())
        counted = [r for r, v in doc['repositories'].items()
                   if v['runtime'] == 'trusted-page-v1' and r not in doc['trustedPageV1Baseline']['repositories']]
        self.assertTrue(counted)
        validate_app_runtime(self.root)

    def test_entry_must_carry_fields(self):
        def drop(d):
            del d['entries'][0]['runtime']
        self.edit('catalogs/blueprints.json', drop)
        with self.assertRaises(ValueError):
            validate_app_runtime(self.root)

    def test_entry_must_match_record(self):
        def flip(d):
            e = next(e for e in d['profiles'] if e['runtime'] == 'trusted-page-v1')
            e['runtime'] = 'restricted-wasm-v1'
        self.edit('catalogs/profile-pointers.json', flip)
        with self.assertRaises(ValueError):
            validate_app_runtime(self.root)

    def test_unrecorded_repository_is_unknown(self):
        self.assertEqual(app_runtime.fields({'repositories': {}}, 'x/y'), app_runtime.UNKNOWN)

    def test_trial_registrations_add_no_trusted_page(self):
        doc = app_runtime.load(ROOT)
        trial = [r for r, v in doc['repositories'].items() if v['basis'] == 'jun-1439-trial-review']
        self.assertEqual(len(trial), 20)
        self.assertTrue(all(doc['repositories'][r]['runtime'] == 'none' for r in trial))

    def test_no_retired_repository_alias(self):
        # KOTOBA-159: every catalog repository is the redirect-resolved name (gh api
        # full_name + repo id, 2026-11-22). No retired transfer alias may come back.
        import repo_redirects  # noqa: E402
        doc = app_runtime.load(ROOT)
        for repository in list(doc['repositories']) + doc['trustedPageV1Baseline']['repositories']:
            self.assertNotIn(repository, repo_redirects.RETIRED, repository)
        bp = json.loads((ROOT / 'catalogs/blueprints.json').read_text())['entries']
        pp = json.loads((ROOT / 'catalogs/profile-pointers.json').read_text())['profiles']
        for e in bp + pp:
            self.assertNotIn(e['repository'], repo_redirects.RETIRED, e['id'])

    def test_retired_alias_refused(self):
        def add(d):
            d['repositories']['network-awai/app-itonami-market'] = {
                'runtime': 'trusted-page-v1', 'handlesUserDataOrExternalComms': 'unknown',
                'basis': 'kotoba-159-evidence'}
        self.edit('catalogs/app-runtime.json', add)
        with self.assertRaises(ValueError):
            validate_app_runtime(self.root)

    def test_adserver_listed_under_canonical_name(self):
        # cloud-itonami/app-itonami-adserver is a retired alias of the same repo id
        # 1295986713; its profiles stay listed under network-awai/app-itonami-adserver.
        doc = app_runtime.load(ROOT)
        self.assertIn('network-awai/app-itonami-adserver', doc['trustedPageV1Baseline']['repositories'])
        self.assertNotIn('cloud-itonami/app-itonami-adserver', doc['repositories'])
        pp = json.loads((ROOT / 'catalogs/profile-pointers.json').read_text())['profiles']
        adserver = [e for e in pp if e['repository'].endswith('app-itonami-adserver')]
        self.assertEqual(len(adserver), 4)
        self.assertTrue(all(e['repository'] == 'network-awai/app-itonami-adserver' for e in adserver))

    def test_kaikei_arbitrage_trusted_page(self):
        # KOTOBA-159: arbitrage build.mjs:40 emits the kotoba.app.client-runtime.v1
        # descriptor with profile trusted-page-v1 (IPC-only CSP); kaikei serves an
        # inert no-send page (site/kaikei/page.cljk) validated as trusted-page-v1 in
        # test/client-runtime-stage.mjs:18. Both were listed pre-cutoff, so the
        # baseline keeps them listed; handles stay undetermined (section B).
        import repo_redirects  # noqa: E402
        doc = app_runtime.load(ROOT)
        for repo in ['cloud-itonami/app-itonami-kaikei', 'cloud-itonami/app-itonami-arbitrage']:
            self.assertEqual(doc['repositories'][repo]['runtime'], 'trusted-page-v1', repo)
            self.assertEqual(doc['repositories'][repo]['basis'], 'kotoba-159-evidence', repo)
            self.assertIn(repo, doc['trustedPageV1Baseline']['repositories'], repo)
            self.assertNotIn(repo, repo_redirects.RETIRED, repo)
        bp = {e['repository']: e for e in json.loads((ROOT / 'catalogs/blueprints.json').read_text())['entries']}
        pp = json.loads((ROOT / 'catalogs/profile-pointers.json').read_text())['profiles']
        self.assertEqual(bp['cloud-itonami/app-itonami-kaikei']['runtime'], 'trusted-page-v1')
        listed = [e for e in pp if e['repository'] in
                  ('cloud-itonami/app-itonami-kaikei', 'cloud-itonami/app-itonami-arbitrage')]
        self.assertEqual(len(listed), 2)
        self.assertTrue(all(e['runtime'] == 'trusted-page-v1' for e in listed))

    def test_market_android_merged_not_deployed(self):
        # KOTOBA-159 runtime-updates.tsv (2026-11-22): market-android is merged, not deployed.
        doc = app_runtime.load(ROOT)
        rec = doc['repositories']['cloud-itonami/app-itonami-market-android']
        self.assertEqual(rec['status'], 'merged-not-deployed')

    def test_unknown_status_refused(self):
        def spoil(d):
            d['repositories']['cloud-itonami/app-itonami-market-android']['status'] = 'live'
        self.edit('catalogs/app-runtime.json', spoil)
        with self.assertRaises(Exception):
            validate_app_runtime(self.root)


if __name__ == '__main__':
    unittest.main()
