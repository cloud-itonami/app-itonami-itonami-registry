# Police intake guide

Look up the country or area by ISO alpha-3 key or by its M49 code in
`police-guide.json`. Follow `workflow.json` to prepare a sourced checklist.
The directory includes 248 country or area identifiers. Blank guidance and
unassessed entries are gaps in research. The snapshot text is in Japanese.

Each country or area contains the scope and status of its official guidance,
the reported intake and follow-up pathways, and any documented public cases.
A case's stage states the outcome actually documented by its source. The
guide's follow-up sections distinguish additional evidence, a portal status
check, a complaint about police conduct and review of an agency decision.

The data is a verbatim snapshot from Awai OS Soudan under Apache 2.0
(`LICENSE.awai-os.txt`). `itonami.json` records its immutable source URL
and SHA-256. For an update, take the new file from its owning repository,
refresh the source pin and hash, bump the workflow version and regenerate
the discovery index. The workflow is a read-only recipe.
