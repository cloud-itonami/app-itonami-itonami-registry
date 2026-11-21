---
name: itonami-statement-reconciliation
description: Reconcile bank, card and expense statements an operator downloaded against a kaikei ledger with the kaikei MCP tools — invoice settlements, matches, transfers and rule-based journal suggestions, posted only after the operator approves each line — without connecting to any bank, card issuer or expense service.
metadata:
  hermes:
    version: 0.1.1
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-kaikei/tree/8e128c838a57d6d7a47f359f6d6f2247afcb8b6d
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-statement-reconciliation

1. **Check the input.**
   - Work only from files the operator downloaded: an OFX/QFX/QBO statement, 全銀 data, a freee, MoneyForward, Xero or QuickBooks Online statement CSV, a bank or card CSV, or a Ramp, Brex, Expensify or BILL export. Do not fetch from a bank, card issuer or any of these services. kaikei has no network access and no credentials, and it makes no payment.
   - Expensify data must be exported with kaikei's own export template; Ramp, Brex and BILL data is the API JSON the operator saved.
   - If the agent's inference rail is remote, ask before handling real statements. They would leave the machine through that rail.
2. **Import.**
   - To reconcile against the operator's books, first get them into a kaikei ledger: call `mcp__kaikei__kaikei_import` with their journal or invoice export, or use a kaikei ledger JSON they exported from the kaikei app.
   - Then call `mcp__kaikei__kaikei_import` with the statement and `ledger` set to that ledger. The statement is added to it; duplicates from an overlapping download are skipped and counted in `added`. Pass `statement_account` (an account id, or `new`) only when the operator says which account the lines belong to.
   - Use `bytes_base64` for Shift_JIS files (全銀 data, most Japanese bank CSV). A file in another currency than the ledger is refused (`currency-mismatch`); one ledger holds one currency.
   - Report the statement accounts, the lines `added` and skipped as duplicates, and every `warnings` entry. A bank or card CSV recognised by an unverified preset says so; pass that on.
   - A statement imported without a ledger has no journals or invoices to match, so only balance checks and the operator's rules apply.
3. **Check.**
   - Call `mcp__kaikei__kaikei_statement_check`. For each account, report the open lines, the `difference` between the statement's last balance and the ledger's, and the first running-balance break if there is one.
   - A break means a download is missing lines or overlaps wrongly; ask the operator for the missing period instead of posting around it.
   - Report the receivable and payable aging when the operator asks about unpaid invoices.
4. **Suggest.**
   - Call `mcp__kaikei__kaikei_statement_suggest`. Present each line's candidates with their strength (3 strong, 2 medium, 1 weak) and reasons.
   - A candidate is a deterministic rule, not a judgement: an amount and name or invoice-number match, an existing entry, a transfer, the operator's rule, or a rule counted from the operator's past journals. Say which.
   - A short payment settles the invoice with the difference as a bank fee. By default that is a return of the sale's consideration (NTA インボイス Q&A 問 30); report the `return-invoice` warning when the difference is 10,000 yen or more.
5. **Post, only what the operator approves.**
   - Call `mcp__kaikei__kaikei_statement_post` with one approval per line the operator chose, using the candidate's `choice`, the operator's own choice, or `"preselected"` when they accept every single strong candidate.
   - Report `posted` and every `skipped` reason. `rate-unknown` means kaikei has no confirmed consumption-tax rate for that date (before 2014-04-01, or reduced-rate items from 2027-04-01); ask the operator for the rate, do not supply one.
   - Call `mcp__kaikei__kaikei_statement_check` again and report the new difference.
6. **Export, if asked.** Call `mcp__kaikei__kaikei_export` with a statement format and `statement_account`, and pass on the `notes`.
7. **State the limits.**
   - Nothing was sent or stored, no bank was contacted and no payment was made.
   - Suggestions and learned rules are kaikei's counting rules over the operator's own data, not a vendor's matching and not a model's inference.
   - This is not 電子帳簿保存法 compliance and not a tax filing.

The tool contracts are pinned in itonami.json and catalogs/sources.json. The server lives in cloud-itonami/app-itonami-kaikei and is enabled only by a profile owner's mcp_servers entry.
