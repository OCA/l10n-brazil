Sends Brazilian payment orders to the bank through its API, using the
[brbank](https://pypi.org/project/brbank/) library and the bank connection of
`l10n_br_bank_connection`. It is the Brazilian provider of
`account_payment_order_api` (OCA/bank-payment).

Each payment line goes in a bank batch of its kind:

- **Boleto** and **guia** (utility bills and taxes with a barcode): from the
  barcode or the digitable line of the line;
- **Pix**: to the Pix key of the line, or to the bank account of the supplier;
- **Pix copy and paste**: from the code of the line, also copied from the payment
  schedule;
- **TED**: to the bank account of the supplier.

The banks are the payment adapters brbank registers, and each one declares what it
pays: a line of another kind stops the order with a message before anything goes to
the bank. The bank answers line by line; the status, the reason and the bank
authentication show on the order, and the payment of a line is posted only when
the bank reports it as paid.

What sending does depends on the bank, and the button says it before the call:

- **Banco do Brasil** and **Itaú**: the payments wait for an approver in the bank
  channel; Odoo follows the approval by checking the bank.
- **Santander**: the bank validates and holds the payments; the money moves with
  **Authorize at the Bank**, for accounting managers, with the user and date in the
  chatter.
- **Bradesco** and **Sicoob**: the money leaves when the bank receives the payment.
- **Inter**: it depends on the approval setting of the account at the bank.

Where the Odoo click can move the money (Santander, Bradesco, Sicoob and Inter), the
mode always requires the second factor of `account_payment_order_api`; at Banco do
Brasil and Itaú it is optional.

Banks without batches get one call per line. A line without an answer becomes
**Unknown** and the next ones are not sent: they are refused as not sent and can
go in a new order. An unknown line is never sent again; Odoo asks the bank for it,
and when there is no identifier to ask (a TED at Bradesco) it stays unknown for a
check against the bank statement.
