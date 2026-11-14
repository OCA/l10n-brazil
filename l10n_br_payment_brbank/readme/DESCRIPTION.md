Issue and follow boletos and Pix charges in several Brazilian banks through
[brbank](https://pypi.org/project/brbank/), a Python library with one adapter per
bank. This module is the Odoo face of the library: one generic payment provider
(`code = brbank`) and one provider record per bank, so a new bank is data and a
credentials screen, not a new module.

Banks delivered as providers (all disabled until configured):

- Boleto: Banco Inter, PinBank, Sicoob, Sicredi, Banco do Brasil, Itaú,
  Bradesco, Santander, BTG Pactual, C6 Bank, Banrisul, Unicred, Caixa and
  Safra.
- Pix (BACEN API, `/cob` and `/cobv`): Banco Inter, Banco do Brasil, Sicoob,
  Sicredi, Itaú, Bradesco, Santander and Efí.

What the module does:

- One bank title per open installment of the invoice, each transaction tied to
  its installment (`move_line_id` of `l10n_br_payment`): issuing again
  never charges twice, and paying out of order settles the right installment.
- Transaction states follow the canonical status of the bank: pending
  registration -> pending, registered -> authorized, settled -> done, written
  off -> canceled, rejected -> error. A transaction is only settled after the
  bank is queried: a webhook never settles anything by itself.
- Fills the digitable line, bar code, Pix copy and paste and TXID that
  `l10n_br_payment` shows on the transaction, the invoice PDF and the portal.
- Bank instructions (due date extension, rebate, protest, write-off) as
  records with the answer of the bank, offered only when the bank declares the
  capability, from the transaction or from the open installment of the invoice.
  What the bank accepts reaches the invoice: the due date of the installment,
  or a credit note for the rebate.
- A generic webhook per provider, protected by a secret token, that stores the
  events and answers at once; the events are processed by a cron triggered
  immediately, which queries the bank.
- A reconciliation cron for every brbank provider, as the safety net of the
  webhooks.
- Credentials readable only by system administrators; certificates go to the
  library only in memory; logs and stored bank answers are masked by the
  library (no name, document, address or PDF of the payer).

The library is asynchronous; the module calls it through a single bridge that
runs each call in a dedicated, short lived event loop.
