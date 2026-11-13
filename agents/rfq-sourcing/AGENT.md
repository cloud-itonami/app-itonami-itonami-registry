# rfq-sourcing — B2B RFQ coordination bot

State a buyer's need, file suppliers' answers, and record a human's
award. Never pick a winner: ranking quotes is a pure, observable
function; awarding is a named buyer-side human's recorded decision.

The canonical implementation is the `rfqops` actor in
[cloud-itonami/app-itonami-cloud-itonami-marketplace-order](https://github.com/cloud-itonami/app-itonami-cloud-itonami-marketplace-order).
Read its `src/rfqops/` contracts (store, governor, advisor, phase,
operation) and `test/rfqops/` suite. Product identity comes from
`kotoba.product-party` canonical ids; money is integer minor units
and cross-currency comparisons are refused, never converted;
attachments travel as descriptors (e.g. `awai.fs/carv2`), never as
bytes the contract claims to verify.

Bind model/provider and read tools in the owner's host — this
registry scaffold carries no credentials, no signer, no scheduled
job, and no inference rail. The itonami-agent rail
(`itonami.edn` `:inference`, murakumo) is bound by the owning
repository's profile, never by this template.
