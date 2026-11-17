#!/usr/bin/env python3
"""Offline catalog, dependency, source and schema checks. Never invokes tools."""
import hashlib
import json
import re
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from build_index import ROOT, entries, frontmatter
from profile_tree import allowed, tree_checksum
from profile_status import load_declared


def read(path):
    return json.loads(path.read_text())


def validate_profile(root, folder, e, side, refs):
    """An Itonami profile entry (ADR 0002): schema, pinned owner files only,
    no credential/memory/state files, and a tree checksum that matches."""
    m = read(folder / 'manifest.json')
    Draft202012Validator(read(root / 'schemas/itonami/profile.schema.json')).validate(m)
    extra = sorted(p.name for p in folder.iterdir() if p.name not in ('manifest.json', 'itonami.json', 'README.md'))
    if extra:
        raise ValueError(f'Profile entry must not copy profile files: {extra}')
    prof = m['profile']
    if m['source'] != f"https://github.com/{prof['repository']}/tree/{prof['commit']}":
        raise ValueError('Profile source differs from its pinned profile commit')
    if side.get('roleKind') != 'profile':
        raise ValueError('Profile itonami.json must declare roleKind profile')
    names = [f['path'] for f in prof['files']]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate profile file')
    if 'SOUL.md' not in names:
        raise ValueError('Profile has no SOUL.md')
    for f in prof['files']:
        if not allowed(f['path']) or '..' in f['path'].split('/'):
            raise ValueError(f"Not a registry profile file: {f['path']}")
    if tree_checksum(prof['files']) != prof['checksum']:
        raise ValueError('Profile tree checksum mismatch')
    pinned = {}
    for ref in side['sourceRefs']:
        src = refs[ref]
        if (src['repository'], src['commit']) == (prof['repository'], prof['commit']):
            pinned.update({f['path']: f['sha256'] for f in src['files']})
    for f in prof['files']:
        if pinned.get(f"{prof['path']}/{f['path']}") != f['sha256']:
            raise ValueError(f"Profile file not pinned in catalogs/sources.json: {f['path']}")


def validate(root=ROOT):
    all_files = [p for p in root.rglob('*') if '.git' not in p.parts and '__pycache__' not in p.parts]
    for p in all_files:
        if p.is_symlink():
            raise ValueError(f'Symlink refused: {p}')
        if p.is_file() and (p.name.startswith('._') or p.name == '.env' or p.suffix in ['.db', '.sqlite', '.jsonl']):
            raise ValueError(f'Runtime/secret/cache artifact refused: {p}')
    schemas = [read(p) for p in sorted((root / 'schemas/hermes').glob('*.json')) if p.name != 'provenance.json']
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas)
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
    schema_by_type = {k: read(root / f'schemas/hermes/{k}.schema.json') for k in ['agent', 'mcp', 'workflow']}
    ext = read(root / 'schemas/itonami.schema.json')
    Draft202012Validator.check_schema(ext)
    ext_validator = Draft202012Validator(ext)
    sources = read(root / 'catalogs/sources.json')
    ext_validator.validate(sources)
    refs = {s['id']: s for s in sources['sources']}
    if len(refs) != len(sources['sources']):
        raise ValueError('Duplicate source identity')
    for source in refs.values():
        if not re.fullmatch(r'[0-9a-f]{40}', source['commit']):
            raise ValueError('Source commit must be immutable')
        for f in source['files']:
            if not re.fullmatch(r'[0-9a-f]{64}', f['sha256']):
                raise ValueError('Source digest missing')
            if Path(f['path']).is_absolute() or '..' in Path(f['path']).parts:
                raise ValueError('Unsafe source path')
            expected = f"https://github.com/{source['repository']}/blob/{source['commit']}/{f['path']}"
            if f['url'] != expected:
                raise ValueError('Source URL differs from pinned identity')
    provenance = read(root / 'schemas/hermes/provenance.json')
    for f in provenance['files']:
        p = root / f['path']
        if hashlib.sha256(p.read_bytes()).hexdigest() != f['sha256']:
            raise ValueError(f'Vendored schema changed: {p}')
    catalog = entries(root)
    identities = {e['type'] + '/' + e['id'] for e in catalog}
    for e in catalog:
        if e['type'] == 'api':
            continue  # self-pinned; validate_apis below (ADR 0005)
        folder = root / e['path']
        side = read(folder / 'itonami.json')
        ext_validator.validate(side)
        if any(ref not in refs for ref in side['sourceRefs']):
            raise ValueError('Unresolved source reference')
        if e['source'] not in [f"https://github.com/{refs[r]['repository']}/tree/{refs[r]['commit']}" for r in side['sourceRefs']]:
            raise ValueError('Entry source differs from provenance')
        if side['authority']['grants'] is not False or side['authority']['default'] != 'blocked':
            raise ValueError('Registry must not grant runtime authority')
        if side['validation']['live'] is not False:
            raise ValueError('Initial entries must not claim live qualification')
        if e['type'] == 'profile':
            validate_profile(root, folder, e, side, refs)
        elif e['type'] == 'skill':
            meta = frontmatter(folder / 'SKILL.md')
            for k in ['name', 'description']:
                if not isinstance(meta.get(k), str) or not meta[k]:
                    raise ValueError('Skill identity missing')
        else:
            m = read(folder / 'manifest.json')
            Draft202012Validator(schema_by_type[e['type']], registry=registry).validate(m)
            for dep in m.get('requires', []) + [d['id'] for d in m.get('dependencies', [])]:
                if dep not in identities:
                    raise ValueError(f'Unresolved dependency: {dep}')
            if e['type'] in ['agent', 'workflow']:
                p = folder / m['entry']
                if Path(m['entry']).is_absolute() or '..' in Path(m['entry']).parts or not p.is_file():
                    raise ValueError('Entry file absent or unsafe')
            if e['type'] == 'workflow':
                ext_validator.validate(read(folder / m['entry']))
                for step in read(folder / m['entry'])['steps']:
                    if any(dep not in identities for dep in step.get('uses', [])):
                        raise ValueError('Unresolved workflow step dependency')
            if e['type'] == 'agent':
                if m.get('tools') != []:
                    raise ValueError('Initial agent scaffolds must not enable tools')
                import yaml
                config = yaml.safe_load((folder / 'templates/hermes/config.yaml').read_text())
                if config.get('toolsets') != []:
                    raise ValueError('Profile scaffold enables tools')
                for example in side.get('examples', []):
                    ext_validator.validate(read(folder / example))
        if any(dep not in identities for dep in side.get('dependsOn', [])):
            raise ValueError('Unresolved supplemental dependency')
    models_schema = read(root / 'schemas/hermes/models.schema.json')
    for path in sorted((root / 'models').glob('*.json')):
        provider = read(path)
        Draft202012Validator(models_schema).validate(provider)
        if provider['id'] != path.stem:
            raise ValueError(f'Model provider id differs from file: {path}')
    tools = read(root / 'catalogs/tools.json')
    ext_validator.validate(tools)
    seen = set()
    for t in tools['tools']:
        if t['id'] in seen:
            raise ValueError('Duplicate provider-qualified tool')
        seen.add(t['id'])
        p = t['provider']
        if p['sourceRef'] not in refs or p['path'] not in [f['path'] for f in refs[p['sourceRef']]['files']]:
            raise ValueError('Unresolved tool source')
        if p['kind'] == 'mcp' and p.get('entry') not in identities:
            raise ValueError('Unresolved MCP provider')
        Draft202012Validator.check_schema(t['inputSchema'])
    external = read(root / 'catalogs/external-registries.json')
    ext_validator.validate(external)
    for r in external['registries']:
        if not re.fullmatch(r'[0-9a-f]{40}', r['commit']):
            raise ValueError('External registry must be pinned')
        if identities.intersection(r['entries']):
            raise ValueError('Duplicates an externally owned entry')
    # Federated index snapshots (ADR 0002): pinned to the registration's commit,
    # metadata only, registry-qualified identities, upstream checksums kept.
    registered = {r['id']: r for r in external['registries']}
    for path in sorted((root / 'catalogs/federated').glob('*.json')):
        snap = read(path)
        reg = snap.get('registry', {})
        if snap.get('schemaVersion') != 'itonami.federated-index.v1' or reg.get('id') != path.stem:
            raise ValueError(f'Malformed federated index: {path.name}')
        if registered.get(path.stem, {}).get('commit') != reg.get('commit'):
            raise ValueError(f'Federated index not pinned to its registration: {path.name}')
        if snap['count'] != len(snap['entries']):
            raise ValueError(f'Federated index count mismatch: {path.name}')
        for e in snap['entries']:
            if e['qualifiedId'] != f"{path.stem}/{e['type']}/{e['id']}":
                raise ValueError(f"Federated identity not qualified: {e['qualifiedId']}")
            if not re.fullmatch(r'sha256:[0-9a-f]{64}', e.get('checksum', '')):
                raise ValueError(f"Federated entry without upstream checksum: {e['qualifiedId']}")
    ext_validator.validate(read(root / 'docs/validation.json'))
    inventory = read(root / 'catalogs/inventory.json')
    inventory_schema = read(root / 'schemas/inventory.schema.json')
    Draft202012Validator.check_schema(inventory_schema)
    Draft202012Validator(inventory_schema).validate(inventory)
    repo_names = [r['repository'] for r in inventory['repositories']]
    # Targeted public-source reviews do not rewrite the dated full-org survey.
    targeted = read(root / 'catalogs/targeted-public-sources.json')
    Draft202012Validator(read(root / 'schemas/targeted-public-sources.schema.json')).validate(targeted)
    targeted_rows = targeted['sources']
    targeted_names = [r['repository'] for r in targeted_rows]
    if len(set(targeted_names)) != len(targeted_names) or set(targeted_names) & set(repo_names):
        raise ValueError('Duplicate targeted public source')
    for row in targeted_rows:
        if not any(s['repository'] == row['repository'] and s['commit'] == row['commit'] for s in refs.values()):
            raise ValueError('Targeted source lacks matching pinned provenance')
    if any(source['repository'] not in repo_names + targeted_names for source in refs.values()):
        raise ValueError('Non-public or unsurveyed registry source refused')
    if len(set(repo_names)) != len(repo_names):
        raise ValueError('Duplicate inventory repository')
    from collections import Counter
    for org in inventory['scope']:
        rows = [r for r in inventory['repositories'] if r['repository'].startswith(org + '/')]
        summary = inventory['summary'][org]
        if summary['publicRepositories'] != len(rows) or summary['totalRepositories'] != len(rows) + summary['privateRepositoriesOmitted']:
            raise ValueError('Inventory coverage count mismatch')
        if summary['scanStatus'] != dict(Counter(r['scanStatus'] for r in rows)) or summary['dispositions'] != dict(Counter(r['disposition'] for r in rows)):
            raise ValueError('Inventory disposition count mismatch')
    expected_registrations = {(refs[r]['repository'], refs[r]['commit'], e['type'] + '/' + e['id']) for e in catalog if e['type'] != 'api' for r in read(root / e['path'] / 'itonami.json')['sourceRefs']}
    observed_registrations = {(r['repository'], e['sourceCommit'], e['entry']) for r in inventory['repositories'] for e in r['registrations']}
    observed_registrations.update((r['repository'], e['sourceCommit'], e['entry']) for r in targeted_rows for e in r['registrations'])
    if expected_registrations != observed_registrations:
        raise ValueError('Inventory registration provenance mismatch')
    reviews = read(root / 'catalogs/candidate-reviews.json')
    review_schema = read(root / 'schemas/candidate-reviews.schema.json')
    Draft202012Validator.check_schema(review_schema)
    Draft202012Validator(review_schema).validate(reviews)
    if reviews['counts'] != dict(Counter(r['decision'] for r in reviews['reviews'])):
        raise ValueError('Candidate review decision count mismatch')
    review_repos = [r['repository'] for r in reviews['reviews']]
    if len(set(review_repos)) != len(review_repos):
        raise ValueError('Duplicate candidate review owner')
    for review in reviews['reviews']:
        if review['repository'] not in repo_names:
            raise ValueError('Non-public candidate review refused')
        if review['reviewedOn'] != reviews['reviewedOn']:
            raise ValueError('Candidate review date mismatch')
        for file in review['evidence']:
            if Path(file['path']).is_absolute() or '..' in Path(file['path']).parts:
                raise ValueError('Unsafe candidate evidence path')
            expected = f"https://github.com/{review['repository']}/blob/{review['commit']}/{file['path']}"
            if file['url'] != expected:
                raise ValueError('Candidate evidence URL differs from pinned identity')
        if review['decision'] == 'registered' and not any(s['repository'] == review['repository'] and s['commit'] == review['commit'] for s in refs.values()):
            raise ValueError('Registered candidate lacks matching source provenance')
    validate_datasets(root)
    validate_actors(root)
    validate_blueprints(root)
    validate_libraries(root)
    validate_apps(root)
    validate_compat(root)
    validate_apis(root, catalog, identities, {r['id']: r for r in external['registries']})
    load_declared(root)
    return len(catalog), len(tools['tools'])


def validate_apis(root, catalog, identities, external):
    """API entries and their classification (ADR 0005): self-pinned shapes, honest
    status, no copied repository files, relations that resolve, counts that agree."""
    schema = read(root / 'schemas/itonami/api.schema.json')
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    apis = {e['id']: e for e in catalog if e['type'] == 'api'}
    for e in apis.values():
        folder = root / e['path']
        extra = sorted(p.name for p in folder.iterdir() if p.name != 'manifest.json')
        if extra:
            raise ValueError(f"API entry must not copy repository files: {e['id']} {extra}")
        m = read(folder / 'manifest.json')
        validator.validate(m)
        pin = m['pin']
        if m['source'] != f"https://github.com/{pin['repository']}/tree/{pin['commit']}" + (f"/{pin['path']}" if 'path' in pin else ''):
            raise ValueError(f"API source differs from its pin: {e['id']}")
        if ('path' in pin) != ('origin' in pin):
            raise ValueError(f"API pin path and origin go together: {e['id']}")
        if (pin['path'] if 'path' in pin else pin['repository'].split('/', 1)[1]) not in (m['id'], f"compat/{m['id']}"):
            raise ValueError(f"API id differs from its repository name: {e['id']}")
        if not m['version'].startswith('1.0.0+' + pin.get('origin', pin)['commit'][:12]):
            raise ValueError(f"API version does not carry its pin: {e['id']}")
        if 'manifest.json' not in {f['path'] for f in pin['files']}:
            raise ValueError(f"API entry without a digested source manifest: {e['id']}")
        if len({f['path'] for f in pin['files']}) != len(pin['files']):
            raise ValueError(f"Duplicate API pinned file: {e['id']}")
        api = m['api']
        if api['routeCount'] != len(api['routes']):
            raise ValueError(f"API route count mismatch: {e['id']}")
        claimed = 'vendorSource' in api or 'upstream' in api
        if (m['status']['vendorConformance'] == 'claimed-by-source') != claimed:
            raise ValueError(f"API vendor conformance status disagrees with its source claim: {e['id']}")
        for target in m['relations']['implementedBy'] + m['relations']['consumedBy']:
            parts = target.split('/')
            if len(parts) == 2 and target not in identities:
                raise ValueError(f"Unresolved API relation: {e['id']} -> {target}")
            if len(parts) == 3 and parts[0] != 'itonami-registry' and parts[0] not in external:
                raise ValueError(f"API relation to an unregistered registry: {e['id']} -> {target}")
    relations = read(root / 'catalogs/api-relations.json')
    Draft202012Validator(read(root / 'schemas/api-relations.schema.json')).validate(relations)
    for r in relations['relations']:
        m = read(root / 'apis' / r['api'] / 'manifest.json') if r['api'] in apis else None
        if not m or any(sorted(r.get(k, [])) != m['relations'][k] for k in ['implementedBy', 'consumedBy']):
            raise ValueError(f"API relation not reflected in its entry: {r['api']}")
    validate_origin_extract(root, apis)
    doc = read(root / 'catalogs/api-classification.json')
    cschema = read(root / 'schemas/api-classification.schema.json')
    Draft202012Validator.check_schema(cschema)
    Draft202012Validator(cschema).validate(doc)
    from collections import Counter
    rows = doc['entries']
    repos = [r['repository'] for r in rows]
    if len(set(repos)) != len(repos):
        raise ValueError('Duplicate classified repository')
    c = doc['counts']
    by_class = Counter(r['class'] for r in rows)
    by_class['unclassified'] += c['privateOmitted']
    reasons = Counter(r['reason'] for r in rows if r['class'] == 'unclassified')
    if c['privateOmitted']:
        reasons['private-repository'] = c['privateOmitted']
    if (c['public'] != len(rows) or c['total'] != len(rows) + c['privateOmitted']
            or c['byClass'] != {k: by_class.get(k, 0) for k in ['api', 'skill', 'profile', 'bot', 'unclassified']}
            or c['unclassifiedByReason'] != dict(reasons) or c['publicByFamily'] != dict(Counter(r['family'] for r in rows))
            or set(doc['reasons']) != set(reasons)):
        raise ValueError('API classification count mismatch')
    classified = {r['entry'].split('/', 1)[1]: r for r in rows if r['class'] == 'api'}
    if set(classified) != set(apis):
        raise ValueError('API classification and api entries disagree')
    for name, r in classified.items():
        pin = read(root / 'apis' / name / 'manifest.json')['pin']
        if 'origin' in pin:
            o = pin['origin']
            if (o['repository'], o['commit'], o['archived']) != (r['repository'], r['commit'], r['archived']) \
                    or r.get('retiredTo') != {'repository': pin['repository'], 'commit': pin['commit'], 'path': pin['path']}:
                raise ValueError(f'API entry pin differs from its classification row: {name}')
            if not re.fullmatch(r'[0-9a-f]{40}', pin['commit']) or not (root / pin['path']).is_dir():
                raise ValueError(f'Internalized API pin does not resolve in this registry: {name}')
        elif (pin['repository'], pin['commit'], pin['archived']) != (r['repository'], r['commit'], r['archived']):
            raise ValueError(f'API entry pin differs from its classification row: {name}')


def validate_compat(root):
    """Compat monorepo (ADR 0006): every compat/<slug>/ is a pinned import of one
    kotoba-lang repository; the index is generated; nothing runs or is granted."""
    from build_compat_index import build as build_compat
    doc = read(root / 'catalogs/compat-sources.json')
    if doc.get('schemaVersion') != 'itonami.compat-sources.v1' or doc['count'] != len(doc['sources']):
        raise ValueError('Malformed compat sources catalog')
    slugs = [s['slug'] for s in doc['sources']]
    if len(set(slugs)) != len(slugs):
        raise ValueError('Duplicate compat slug')
    folders = sorted(p.name for p in (root / 'compat').iterdir() if p.is_dir())
    if folders != sorted(slugs):
        raise ValueError('compat/ folders differ from catalogs/compat-sources.json')
    for s in doc['sources']:
        if not re.fullmatch(r'[0-9a-f]{40}', s['commit']):
            raise ValueError(f"Compat source commit must be immutable: {s['slug']}")
        if s['repository'] != f"{doc['organization']}/{s['slug']}" or not s['pushed']:
            raise ValueError(f"Compat source not a pinned public repository commit: {s['slug']}")
        folder = root / 'compat' / s['slug']
        if (folder / '.github').exists() or (folder / '.git').exists():
            raise ValueError(f"Compat tree carries CI or git metadata: {s['slug']}")
        if read(folder / 'manifest.json').get('kind') != 'compat':
            raise ValueError(f"Compat manifest kind differs: {s['slug']}")
    build_compat(root, check=True)


def validate_datasets(root):
    """Dataset source catalogs (ADR 0004): references only, pinned, never a Hermes entry."""
    schema = read(root / 'schemas/dataset-sources.schema.json')
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    paths = sorted((root / 'catalogs/datasets').glob('*.json'))
    if not paths:
        raise ValueError('Dataset catalogs missing')
    seen_repos = set()
    for path in paths:
        doc = read(path)
        validator.validate(doc)
        if doc['family'] != path.stem or doc['count'] != len(doc['entries']):
            raise ValueError(f'Dataset catalog family or count mismatch: {path.name}')
        for e in doc['entries']:
            if not e['id'].startswith(doc['family'] + '/'):
                raise ValueError(f"Dataset entry outside its family: {e['id']}")
            if e['repository'] in seen_repos:
                raise ValueError(f"Duplicate dataset repository: {e['repository']}")
            seen_repos.add(e['repository'])
            if (e['digestStatus'] == 'verified') != bool(e['payload']):
                raise ValueError(f"Dataset digest status disagrees with payload: {e['id']}")
            if len({p['path'] for p in e['payload']}) != len(e['payload']):
                raise ValueError(f"Duplicate dataset payload path: {e['id']}")
        ids = [e['id'] for e in doc['entries']]
        if len(set(ids)) != len(ids):
            raise ValueError(f'Duplicate dataset id: {path.name}')


def validate_actors(root):
    """Actor source catalog (ADR 0011): references only, pinned, never a Hermes entry, grants nothing."""
    path = root / 'catalogs/actors.json'
    schema = read(root / 'schemas/actor-sources.schema.json')
    Draft202012Validator.check_schema(schema)
    doc = read(path)
    Draft202012Validator(schema).validate(doc)
    if doc['count'] != len(doc['entries']):
        raise ValueError('Actor catalog count mismatch')
    ids, repos = set(), set()
    for e in doc['entries']:
        if e['id'] in ids or e['repository'] in repos:
            raise ValueError(f"Duplicate actor entry: {e['id']}")
        ids.add(e['id'])
        repos.add(e['repository'])
        if (e['digestStatus'] == 'verified') != bool(e['payload']):
            raise ValueError(f"Actor digest status disagrees with payload: {e['id']}")
        if len({p['path'] for p in e['payload']}) != len(e['payload']):
            raise ValueError(f"Duplicate actor payload path: {e['id']}")


def validate_blueprints(root):
    """Blueprint source catalog (ADR 0012): references only, pinned, never a Hermes entry, grants nothing."""
    path = root / 'catalogs/blueprints.json'
    schema = read(root / 'schemas/blueprint-sources.schema.json')
    Draft202012Validator.check_schema(schema)
    doc = read(path)
    Draft202012Validator(schema).validate(doc)
    if doc['count'] != len(doc['entries']):
        raise ValueError('Blueprint catalog count mismatch')
    ids, repos, bps = set(), set(), set()
    for e in doc['entries']:
        if e['id'] in ids or e['repository'] in repos:
            raise ValueError(f"Duplicate blueprint entry: {e['id']}")
        ids.add(e['id'])
        repos.add(e['repository'])
        bps.add(e['keys']['blueprint'])
        paths = [p['path'] for p in e['payload']]
        if len(set(paths)) != len(paths):
            raise ValueError(f"Duplicate blueprint payload path: {e['id']}")
        if 'blueprint.edn' not in paths:
            raise ValueError(f"Blueprint entry lacks blueprint.edn: {e['id']}")


def validate_libraries(root):
    """Library source catalog (ADR 0014): references only, pinned, never a Hermes entry, grants nothing."""
    doc = read(root / 'catalogs/libraries.json')
    schema = read(root / 'schemas/library-sources.schema.json')
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(doc)
    if doc['count'] != len(doc['entries']):
        raise ValueError('Library catalog count mismatch')
    ids, repos = set(), set()
    for e in doc['entries']:
        if e['id'] in ids or e['repository'] in repos:
            raise ValueError(f"Duplicate library entry: {e['id']}")
        ids.add(e['id'])
        repos.add(e['repository'])
        paths = [p['path'] for p in e['payload']]
        if len(set(paths)) != len(paths) or 'deps.edn' not in paths:
            raise ValueError(f"Library payload invalid: {e['id']}")


def validate_apps(root):
    """App source catalog (ADR 0015): references only, pinned, never a Hermes entry, grants nothing."""
    doc = read(root / 'catalogs/apps.json')
    schema = read(root / 'schemas/app-sources.schema.json')
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(doc)
    if doc['count'] != len(doc['entries']):
        raise ValueError('App catalog count mismatch')
    ids, repos = set(), set()
    for e in doc['entries']:
        if e['id'] in ids or e['repository'] in repos:
            raise ValueError(f"Duplicate app entry: {e['id']}")
        ids.add(e['id'])
        repos.add(e['repository'])
        paths = [p['path'] for p in e['payload']]
        if len(set(paths)) != len(paths) or (e['digestStatus'] == 'verified') != bool(paths):
            raise ValueError(f"App payload invalid: {e['id']}")


def validate_origin_extract(root, apis):
    """The public origin-domain extract (ADR 0005 §4): domain facts for api entries only, each
    reflected in exactly that entry; every other api entry stays unverified."""
    doc = read(root / 'catalogs/origin-domains.json')
    schema = read(root / 'schemas/origin-domains.schema.json')
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(doc)
    if doc['count'] != len(doc['entries']):
        raise ValueError('Origin extract count mismatch')
    facts = {}
    for e in doc['entries']:
        if e['api'] in facts:
            raise ValueError(f"Duplicate origin fact: {e['api']}")
        if e['api'] not in apis or e['repository'] != (lambda pin: pin.get('origin', pin)['repository'])(read(root / 'apis' / e['api'] / 'manifest.json')['pin']):
            raise ValueError(f"Origin fact for no api entry: {e['api']}")
        rev = '.'.join(reversed(e['domain'].split('.')))
        if e['reverseDomain'] != rev:
            raise ValueError(f"Reverse domain is not the reversed domain: {e['api']}")
        prefix = rev.replace('.', '-')
        if e['nameMatchesDomain'] != (e['api'] == prefix or e['api'].startswith(prefix + '-')):
            raise ValueError(f"Name match flag is wrong: {e['api']}")
        facts[e['api']] = e
    for rid in apis:
        origin = read(root / 'apis' / rid / 'manifest.json')['api']['origin']
        fact = facts.get(rid)
        if fact is None and origin['status'] != 'unverified':
            raise ValueError(f'Origin recorded without a fact in the extract: {rid}')
        if fact is not None and (origin['status'], origin.get('domain'), origin.get('reverseDomain'), origin.get('nameMatchesDomain')) != (
                'recorded', fact['domain'], fact['reverseDomain'], fact['nameMatchesDomain']):
            raise ValueError(f'Origin differs from the extract: {rid}')


if __name__ == '__main__':
    count, tools = validate()
    print(f'Validated {count} entries and {tools} tool references; no execution performed')
