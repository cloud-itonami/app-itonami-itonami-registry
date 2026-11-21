---
name: itonami-ledger-statements
description: Build a trial balance, P&L and balance sheet from accounting exports an operator already holds (MoneyForward, freee, Yayoi, QuickBooks Online, Xero) with the kaikei MCP tools, without connecting to any accounting service.
metadata:
  hermes:
    version: 0.1.3
    author: cloud-itonami
    source: https://github.com/cloud-itonami/app-itonami-kaikei/tree/8e128c838a57d6d7a47f359f6d6f2247afcb8b6d
    compatibility:
      hermes: '*'
      desktop: '*'
---

# itonami-ledger-statements

1. **Check the input.**
   - Confirm the input is a file the operator provided: a journal CSV, or QuickBooks or Xero API JSON. Do not fetch from MoneyForward, freee, Yayoi, QuickBooks or Xero. kaikei has no network access and no credentials.
   - If the agent's inference rail is remote, ask before handling a real ledger. The ledger would leave the machine through that rail.
2. **Import.**
   - Call `mcp__kaikei__kaikei_import`. Use `text` for UTF-8 files and `bytes_base64` for Shift_JIS files.
   - Pass `currency` when the file does not say. This applies to Xero responses and to QuickBooks or Xero CSV. Pass `date_order` when the operator knows the region's date order.
   - Report `entries`, `rejected` and every `warnings` entry. Do not drop them.
3. **Validate.**
   - Call `mcp__kaikei__kaikei_validate`.
   - If `unclassified_accounts` is not empty, the P&L and balance sheet are incomplete. Ask the operator which class each account belongs to; do not guess. Set the `class` of those accounts in the ledger, then validate again.
4. **Report.**
   - Call `mcp__kaikei__kaikei_report` with the period the operator asked for. Use `shape` kaikei for a Japanese staged-profit P&L, qbo or xero when the operator wants that vendor's report shape.
   - Cite the totals, and the `bs_difference` when it is not 0.
5. **Convert, if asked.** Call `mcp__kaikei__kaikei_export` or `mcp__kaikei__kaikei_convert`. Pass on the `notes`, which list fields the target format cannot hold.
6. **State the limits.**
   - The class mapping, staged profit and retained-earnings rules are kaikei's, not a vendor's calculation.
   - Nothing was sent or stored.
   - This is not 電子帳簿保存法 compliance and not a tax filing.

The tool contracts are pinned in itonami.json and catalogs/sources.json. The server lives in cloud-itonami/app-itonami-kaikei and is enabled only by a profile owner's mcp_servers entry.
