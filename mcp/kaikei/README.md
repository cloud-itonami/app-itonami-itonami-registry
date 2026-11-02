# kaikei MCP

## Direct financial connections: discovery status

As of 2026-11-02, this registry entry discovers an **offline file-processing**
MCP server. It does not connect to any financial institution. The following
are provider-side capabilities and research leads, not capabilities of the
pinned kaikei server or evidence that an import or connection was tested:

| Service | Provider-side evidence | Direct connection status |
|---|---|---|
| Rakuten Bank, personal and business | [Account and transaction inquiry API](https://www.rakuten-bank.co.jp/business/rules/api-service.html); the bank describes services offered through contracted external service companies. | kaikei access, agreement, authorization, browser access and legal requirements unverified. |
| Rakuten Card | [Member CSV download](https://www.rakuten-card.co.jp/e-navi/p/rc/e-navi/statement/popup2.html). | Official direct read-only API for the user's statements unverified. |
| Rakuten Pay | [Payment history in the app](https://pay.rakuten.co.jp/agreement/). | Official direct read-only API and file export unverified. |
| PayPay personal | [Transaction-history CSV](https://paypay.ne.jp/help/c0447/); excludes some transaction statuses. | Official direct consumer-history API unverified. |
| PayPay merchant | [Payment details by merchant-issued ID](https://developer.paypay.ne.jp/products/docs/nativepayment). | A single merchant-payment lookup is not a consumer transaction-history feed; kaikei integration unverified. |
| Diners | [Personal statement CSV](https://www.diners.co.jp/ja/usage/cyber.html); [corporate statement CSV](https://www.diners.co.jp/ja/corporate/ccol/index.html), subject to card and access conditions. | Official direct read-only API unverified. |
| JAL Card | [Partner-specific member services](https://jalcardfaq.jal.co.jp/--68fb5e92c8b75b4a1de3daef); [NICOS statement rules](https://jalcard.jal.co.jp/admission/mdc_webmeisai.html) describe PDF or CSV. | JCB offers a partner API; kaikei's access is unverified. Other issuer APIs are unverified. |
| SoftBank corporate | [Billing and call-detail CSV](https://www.softbank.jp/support/faq/view/10271). | Official direct read-only API and personal-account coverage unverified. |
| docomo corporate / d-card | [Corporate billing CSV](https://gorikan.billing.smt.docomo.ne.jp/bbilling/html/onlinemanual03.pdf); [d-card and d-pay histories differ](https://service.smt.docomo.ne.jp/keitai_payment/app/help/detail/0900.html). | Official direct read-only API and account-specific coverage unverified. |

JAL Card routes by **issuing partner**, not payment-network brand: JAL Visa,
Mastercard, TOKYU POINT ClubQ and American Express use Mitsubishi UFJ NICOS;
JAL JCB and OP Credit use JCB; JAL Diners uses Sumitomo Mitsui Trust Club;
JAL Suica uses Viewcard. Confirm the actual card and issuer before selecting a
format. [JAL's issuer list](https://jalcardfaq.jal.co.jp/--68fb5e92c8b75b4a1de3daef)
is the source for these routes, not a claim that kaikei has qualified them.

[MyJCB's external connection service](https://www.jcb.co.jp/myjcb/pop/external.html)
provides approved partner companies with API access to some information after
customer consent, with card and service restrictions. Its published partner
list does not establish access for kaikei. API specifications, eligibility,
contract, authentication and a browser-compatible flow must be verified
before implementing a connector. [MyJCB's CSV download](https://j-faq.jcb.co.jp/faq/show/357?site_domain=default)
is limited to finalized statements and excludes some corporate-user and family
card login roles; other JCB products may differ.

For Rakuten Bank, the [published review criteria](https://www.rakuten-bank.co.jp/policy/cooperation_criteria.html)
describe a review, agreement, contract-specified tests and usage fees for
electronic payment service providers. The [customer terms](https://www.rakuten-bank.co.jp/business/rules/api-service.html)
describe identity verification when first connecting. They do not establish
that an independently operated kaikei browser app qualifies, nor do they
publish a usable OAuth endpoint or a tested browser CORS policy here.

The PayPay merchant API's documented payment-details operation looks up one
`merchantPaymentId`; the developer guide identifies an API key and secret in
its authentication failures. This is not a documented way to list a consumer's
spending or an entire merchant's transaction history. A static browser app
must not embed such a secret; client eligibility and an owner-device approach
remain unverified. See [PayPay's guide](https://developer.paypay.ne.jp/products/docs/nativepayment).

The current kaikei build declares Scittle sources, not the canonical
`kotoba-client-runtime.js`. A future live adapter remains blocked until the
canonical implementation is reviewed, the builder uses that exact source,
and the host, declarations, trusted per-operation consent and endpoint-specific
transport are verified. No standalone consent logic is supplied by this entry.

No entry here grants authority to contact a provider or process a statement.
Account aggregation by a third party is not the current project direction.
Use the operator's local files and check format warnings, missing periods,
currency and overlapping card, wallet, bank and billing records. Do not send
real financial data to a remote inference service without separate approval.
For ongoing work and qualification criteria see [JUN-765](https://linear.app/kotobalabs/issue/JUN-765).

This is the stdio MCP server for [kaikei](https://github.com/cloud-itonami/kaikei), an itonami dapp for accounting ledgers, invoices and bank statements. The dapp is also published at https://itonami.cloud/sites/app/kaikei/.

kaikei reads journal exports from MoneyForward クラウド会計, freee 会計, 弥生会計, QuickBooks Online and Xero, and builds a trial balance, P&L and balance sheet. It also handles invoices: it reads and writes Xero, QuickBooks Online, freee請求書 and MoneyForward クラウド請求書 invoices (JSON and import CSV), reads Zoho Invoice and FreshBooks invoices, checks the contents a Japanese qualified invoice must state, and posts invoices as receivable or payable entries. It reads bank and card statements the user downloaded and Ramp, Brex, Expensify and BILL exports, reconciles them against the ledger, and suggests invoice settlements, matches and journals for each line. It posts only the lines the user approved. Every tool is a pure function over the text or ledger the caller passes:

| tool | does |
|---|---|
| `kaikei_import` | Reads a journal or invoice export and returns a `kaikei.ledger.v1` ledger with checks and warnings. Journals: MoneyForward 仕訳帳 CSV, freee 仕訳 CSV, 弥生インポート形式, QuickBooks Online Account/JournalEntry JSON or journal CSV, Xero Accounts/Journals/ManualJournals JSON or manual journal CSV. Invoices: Xero Invoices JSON and invoice/bill CSV, QuickBooks Online Invoice/Bill JSON and invoice CSV, freee請求書 CSV and API JSON, MoneyForward クラウド請求書 CSV and API v3 JSON, Zoho Invoice JSON, FreshBooks invoice/bill JSON. Statements: OFX/QFX/QBO bank and card statements (SGML or XML), 全銀 入出金取引明細 and 振込入金明細 (fixed-length or CSV), freee, MoneyForward, Xero and QuickBooks Online statement CSV, and bank or card CSV recognised from its header. Expense and AP: Ramp transactions, reimbursements and bills JSON, Brex card transactions and reimbursement expenses JSON, Expensify CSV exported with kaikei's template, BILL v3 bills JSON. Also a kaikei ledger. Shift_JIS files go in as `bytes_base64`. With `ledger`, the file is added to that ledger, as the app's append import does: duplicates are skipped and counted in `added`, `statement_account` picks the statement account, and a file in another currency is an error. Invoices and statement lines are imported, not posted. |
| `kaikei_validate` | Checks that the balance sheet balances and lists unclassified accounts and invalid entries. Invalid means unbalanced, negative, missing an account or with a bad date. |
| `kaikei_report` | Returns a trial balance, P&L or balance sheet for a period, in kaikei's own JSON or in the shape of the QuickBooks Online Report or Xero Reports responses. |
| `kaikei_export` | Writes a ledger in the journal and invoice formats above, or one statement account (`statement_account`) as freee, MoneyForward, Xero or QuickBooks Online statement CSV. Shift_JIS output comes back in base64, and fields the format cannot hold are listed in `notes`. |
| `kaikei_convert` | Runs import followed by export. |
| `kaikei_invoice_totals` | Per-rate consideration and consumption tax for invoice lines, rounded once per invoice per rate (消費税法施行令 70 条の 10), and each line's share of the tax. Needs no ledger. |
| `kaikei_invoice_check` | For each invoice in a ledger: missing qualified-invoice contents, differences between the stated tax and one rounding per rate, the transitional deduction percent for purchases from unregistered sellers, and whether it can be posted. |
| `kaikei_invoice_post` | Posts issued or paid invoices as receivable / sales / output tax (or the purchase side) entries and returns the new ledger. Skips drafts, voids, invoices with withholding and invoices already in the ledger. |
| `kaikei_statement_check` | For each statement account: line counts by status (open, posted, matched, excluded), the statement's last balance against the ledger account's balance on that date, and the first line where the running balance breaks. Also a receivable and payable aging in 30-day buckets from the due date. |
| `kaikei_statement_suggest` | Candidates for each open line, without changing the ledger: invoices the payment settles (exact, short by a bank fee, partial, or several invoices of one customer), journal entries to match, transfers between statement accounts, and journals from the user's rules and from rules learned from the user's own past journals. Each has a strength (3 strong, 2 medium, 1 weak), its reasons and a `choice`. |
| `kaikei_statement_post` | Posts only the approved lines, each with its `choice`: settle invoices, match an entry, post a transfer, post to an account with consumption tax split at the date's rate, or exclude the line. `"preselected"` takes the single strong candidate. Returns the new ledger; lines without an approval are untouched. |

How these tools handle the data:

- Nothing is sent to an accounting service or anywhere else, and nothing is stored.
- Amounts are integers in the currency's minor unit, using ISO 4217 exponents. A value with more decimal places than the currency allows is rejected, not rounded.
- An account kaikei cannot classify stays unclassified and is left out of the P&L and balance sheet; it is never guessed.
- The class mapping and the staged-profit and retained-earnings rules are kaikei's own. They do not reproduce any vendor's calculation.
- A registration number is checked for its form (T + 13 digits) only. The NTA publication site is not queried, and an invoice is never certified as qualified.
- Statements come only from files the user downloaded. kaikei connects to no bank, card issuer, Ramp, Brex, Expensify or BILL, does no account aggregation and makes no payment. Ramp, Brex, Expensify and BILL data is read only.
- Only the MUFG BizSTATION CSV preset is checked against the bank's published layout. The other bank and card presets are marked unverified, and an import with one says so in `warnings`.
- A short payment's difference is booked as a bank fee by the ledger's setting: by default as a return of the sale's consideration (account 支払手数料, NTA インボイス Q&A 問 30), or as a purchase or a discount, per customer. A date without a confirmed rate (before 2014-04-01, or reduced-rate items from 2027-04-01) is not guessed; the line is skipped as `rate-unknown` until the choice gives a rate.
- To reconcile a statement against books, pass the books' ledger to `kaikei_import` as `ledger` together with the statement. The ledger JSON carries the journals, invoices, statement lines and rules between calls; a ledger exported from the browser app works the same way.
- Learned rules come from the user's own past journals in the ledger, by a fixed counting rule. Nothing is inferred by a model, and a suggestion is never posted without an approval.
- The tools run on the same `.cljk` adapter as the browser app. That adapter agrees with the wasm guest `aiueos/kaikei_journal.cljk` on the repository's 192-row parity table (journal checks, financial statements, invoice tax, consumption-tax rates by date, statement balances and matching levels). The guest itself is not loaded here.

## Use from an itonami agent profile

```yaml
mcp_servers:
  kaikei:
    command: kbb
    args: ["/absolute/path/to/kaikei/bin/kaikei-mcp"]
```

The tools appear as `mcp__kaikei__kaikei_import` and so on. itonami-agent does not start MCP subprocesses on peer runs.

The tools are pure, but a model-driven agent turn is not local. A ledger passed to an agent whose inference rail is remote leaves the machine through that rail. Use synthetic or consented data there.

The first launch resolves the pinned `kotoba-lang/text` git dependency into `~/.gitlibs` over the network and creates a `.nbb/` cache in the checkout. Later launches only read.

Registering this entry enables nothing. A profile owner has to add the `mcp_servers` entry.

Status: source-inspected and protocol-tested through the itonami-agent MCP client (`discover`/`call`) on synthetic fixtures, all 11 tools. A model-driven agent turn has not been tested.
