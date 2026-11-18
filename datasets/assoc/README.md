# Association source snapshots

The 81 folders are keyed by the suffix of each `assoc/<id>` in
[`catalogs/datasets/assoc.json`](../../catalogs/datasets/assoc.json). Each contains
the original, byte-for-byte `organization.edn`, `blueprint.edn`,
`schema/association-rule.edn` and `data/datascript-tx.edn` from its recorded
upstream commit. The catalog records each upstream identity, commit and file
digest. The original repositories used the same [AGPL-3.0 license](LICENSE.txt).
The original repository names are historical provenance.

The static build checks every retained file against its catalog SHA-256 and
publishes the verified rule files beside the viewer. The source snapshot is
dated; source links in the records refer to the organizations or their archives.
