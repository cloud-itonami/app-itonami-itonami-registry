---
name: itonami-invoices
description: Draft, import, check and post invoices with the kaikei MCP tools — per-rate consumption tax rounded once per invoice per rate, the contents a Japanese qualified invoice must state, and receivable or payable journal entries — without connecting to any invoicing service or the NTA.
metadata:
  hermes:
    version: 0.1.2
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-kaikei/tree/8e128c838a57d6d7a47f359f6d6f2247afcb8b6d
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-invoices

1. **Check the input.**
   - Work only from invoices or lines the operator provided: an export from Xero, QuickBooks Online, freee請求書, MoneyForward クラウド請求書, Zoho Invoice or FreshBooks, a kaikei ledger, or lines typed by the operator. Do not fetch from any of these services. kaikei has no network access and no credentials.
   - If the agent's inference rail is remote, ask before handling real invoices. They would leave the machine through that rail.
2. **Draft totals, if asked.**
   - Call `mcp__kaikei__kaikei_invoice_totals` with the lines (amount, tax rate in percent, `reduced` for the Japanese reduced rate), `tax_mode` and the `rounding` the operator uses.
   - The tax is computed once per invoice per rate (消費税法施行令 70 条の 10). `line_tax` splits it over the lines; the split is kaikei's rule, not a legal requirement.
3. **Import.**
   - Call `mcp__kaikei__kaikei_import`. Use `text` for UTF-8 files and `bytes_base64` for Shift_JIS files (MoneyForward CSV).
   - Report `invoices`, `rejected`, `skipped` and every `warnings` entry. Skipped invoices (credit notes, other currencies, two taxes on a line, invoice-wide discounts) are not in the ledger.
4. **Check.**
   - Call `mcp__kaikei__kaikei_invoice_check`. Report each invoice's `problems` with their messages.
   - A registration number is checked for its form (T + 13 digits) only. Never say it is valid or registered; the NTA was not queried.
   - For a purchase invoice without a registration number, report `deduction_percent` (the transitional measure) as an estimate, not a tax computation.
   - Never call an invoice qualified. Say which required contents were found missing.
5. **Post, only after the operator confirms.**
   - Call `mcp__kaikei__kaikei_invoice_post`, with `invoice_ids` when the operator chose specific invoices. Drafts and voids are not posted.
   - Report `posted` and every `skipped` reason. An invoice whose journal is already in the ledger (for example from Xero Journals) is skipped, not posted twice.
6. **Export or convert, if asked.** Call `mcp__kaikei__kaikei_export` or `mcp__kaikei__kaikei_convert` with an invoice format. Pass on the `notes`; for example, Xero lines not from Xero carry placeholder tax types (KAIKEI-10) that must be replaced before upload.
7. **State the limits.**
   - Nothing was sent or stored, no invoice was delivered, and the NTA publication site was not queried.
   - This is not a tax filing and not a qualified-invoice certification.

The tool contracts are pinned in itonami.json and catalogs/sources.json. The server lives in cloud-itonami/app-itonami-kaikei and is enabled only by a profile owner's mcp_servers entry.
