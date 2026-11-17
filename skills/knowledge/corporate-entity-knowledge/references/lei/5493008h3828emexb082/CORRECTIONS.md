# Corrections carried from an unmerged branch

Entity: LEI 5493008H3828EMEXB082 (cloud-itonami-lei-5493008h3828emexb082, now deleted).

`citations.edn` is the citation catalog (`facts/catalog.edn`, about 90 rows: what each fact was checked against, with the
URL and the substring the check expects) **with the corrections of the unmerged branch `agent/maturity-ingest-citations`
applied**. The branch (5 commits, 2026-08-20, tip e8f2d573) diverged from main (merge base 7a30891d); it was merged onto
main (a clean three-way merge, no conflicts) and the resulting catalog is carried here. Nothing else in this folder was
changed: `facts.edn`, `blueprint.edn` and `tos.journal.edn` are verbatim and none of them contained the corrected text.

What the corrections say, so an answer can use them:

- The GLEIF child count ("six direct children") is a **point-in-time count, true on 2026-08-20**. If it differs now,
  check whether the group structure changed before suspecting the catalog.
- Row id `gleif-isin-us-adr` was renamed `gleif-isin-us-listed`: calling the US instrument an ADR was an unverified
  inference; GLEIF only says it maps the US-domiciled instrument US03524A1088 to the same LEI.
- Companies House (company 11642143): six rows are affected, five of six DRIFTED, and the incorporation date stands only
  because that company was incorporated the same day (a weak discriminator, kept and labelled).
- The Belgian register (KBO) sometimes serves a captcha challenge under repeated lookups; a check must report that as
  "could not answer" (BLOCKED), not as a dropped fact. Each distinct URL is fetched once.

Not carried (kept only in the git mirror of the deleted repository): the branch's `README.md` text, the new
`tools/verify_archive.cljs` and the `tools/verify_citations` changes. Those are tooling for re-checking the catalog, not
knowledge about the company.
