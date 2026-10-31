DDA inbox for Odoo: the boletos that banks register against the CNPJ of your
company arrive by themselves, each one with its vendor, a suggested payable
title and **one recommended action**, so the usual case is solved in one click.

This is the backend core. It does not depend on any bank library: a glue module
(for instance one that reads the API of a bank) or a DDA return file read with
`l10n_br_cnab_structure` feeds it through `_dda_upsert`.

What the module does:

- Boleto model (`l10n_br_dda.debit`) with chatter, one record per payer CNPJ and
  digitable line, shared by every source (API connection, CNAB file, manual).
- Matching with a score for suggestions and a strict rule for the automatic link:
  same full CNPJ, exact amount, same due date, same document number when both
  sides have one, and a single candidate. Two equal installments never link by
  themselves.
- Assignments (guarantor or registered assignee), root CNPJ, N:1 installments
  and tolerance of days and amount are suggestions only.
- Alerts: unknown vendor, no title, possible duplicate, assignment. A boleto
  without title and with an unknown vendor is blocked for payment until an
  approver records the verification.
- Actions with undo: link, create a draft vendor bill, ignore, verify and add to
  a payment order. Nothing edits an invoice: the difference of amount goes to
  the write-off (interest, fine and discount of the payment line).
- Bridge to `l10n_br_account_payment_order`: the digitable line, the bar code
  and the difference travel to the `account.payment.line`, so the CNAB 240
  payment file (Segment J) can be generated.
- Import of a DDA return file: the layout is data in `l10n_br_cnab_structure`
  (structure marked as DDA return); the demo brings a **simulated** one.
