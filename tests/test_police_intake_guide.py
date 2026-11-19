import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / 'workflows' / 'police-intake-guide'


def read(path):
    return json.loads(path.read_text())


class PoliceIntakeGuideTest(unittest.TestCase):
    def test_bundled_snapshot_matches_the_pinned_awai_os_data(self):
        supplemental = read(ENTRY / 'itonami.json')
        sources = {row['id']: row for row in read(ROOT / 'catalogs' / 'sources.json')['sources']}
        source = sources[supplemental['sourceRefs'][0]]
        self.assertEqual(source['repository'], 'network-awai/awai-os')
        pin = next(file for file in source['files']
                   if file['path'] == 'apps/soudan/src/police-guide.json')
        outputs = supplemental['outputs']
        data = (ENTRY / outputs['data']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), pin['sha256'])
        self.assertEqual(outputs['sha256'], pin['sha256'])
        self.assertEqual(outputs['dataSource'], pin['url'])
        self.assertEqual(json.loads(data)['schemaVersion'], 'itonami.police-intake-guide.v1')

    def test_workflow_is_read_only(self):
        self.assertFalse(read(ENTRY / 'workflow.json')['automaticExecution'])
        self.assertEqual(read(ENTRY / 'manifest.json')['permissions'], ['filesystem:read'])
        self.assertFalse(read(ENTRY / 'itonami.json')['authority']['grants'])
