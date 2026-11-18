# ADR 0020 Association snapshots in the Registry

Status: accepted, 2026-11-18 (owner decision, JUN-1361). Extends ADR 0004
for the 81 existing association datasets.

The Registry holds byte-identical copies of each pinned association's
organization metadata, blueprint, association schema, and DataScript records
under `datasets/assoc/`. The original GitHub names and commits remain as
historical provenance. The original AGPL-3.0 license applies to the snapshots.

The website build checks every file against the dataset catalog before producing
the viewer. The static output carries a relative link to the verified rule bytes
and preserves original citations. Building and downloading the bundled data do
not contact the old repositories. The source citations may need network access
when the reader follows them. The legacy dataset catalog refresh preserves the
association catalog.

The 81 source repositories' retirement is tracked separately after migration,
consumer cutover and recovery verification. The Registry snapshot is the data
source; recovery bundles retain Git history and refs outside the site build.
