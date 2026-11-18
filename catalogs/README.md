# Supplemental discovery

These files supplement the Hermes-format index. tools.json identifies tools by provider and native input schema; it is not a tool installer or an authority grant. sources.json pins derivation inputs, with hashes of the original files, not copies of profiles. external-registries.json describes immutable references that need a federation-aware consumer. Generic Hermes clients are not expected to consume these Itonami extensions.

 inventory.json surveys public default-branch filename markers and records selected/deferred ownership decisions. Its snapshot commit differs from a curated entry sourceCommit when that entry intentionally retains an earlier pinned derivation. Private repositories appear only as aggregate counts. Full tree survey does not mean every source file was semantically reviewed.

candidate-reviews.json records the separately dated review of previously pending owners. It pins evidence identities and ownership/registration decisions without copying the original profiles or claiming runtime qualification. The original whole-organization inventory remains dated; registration and review relationships may reference newer source commits.

`targeted-public-sources.json` records specifically reviewed public owners beyond the dated full-organization inventory. It does not assert a full survey of additional organizations. Its pinned registrations are validated alongside inventory provenance.

`datasets/{lei,assoc,municipality}.json` index keyed data repositories of the cloud-itonami organization by pinned commit and file sha256 (ADR 0004). They are references, not copies, are not in `index.json`, and change no owning repository. `unverified` entries have no digests because the builder had no local commit object. Regenerate with `scripts/build_dataset_catalog.py --clones <dir>`.

`actors.json` indexes public Kotoba actor repositories by pinned commit and identity-file sha256 (ADR 0011). It is a reference, not a copy, is not in `index.json`, grants no authority, and changes no owning repository. Regenerate with `scripts/build_actor_catalog.py`.

`datasets/lei.json` (185 entries) and `datasets/municipality.json` (62 entries): their repositories were deleted on 2026-11-17 after the substance moved into `skills/knowledge/corporate-entity-knowledge` (ADR 0017) and `skills/knowledge/municipal-ordinance-knowledge` (ADR 0018). The pins and digests stay as historical provenance of those skills; the repository URLs no longer resolve. Read the data from the skills, not from these catalogs.
