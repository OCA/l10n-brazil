Issuing:

- Post a customer invoice whose payment mode generates boletos with a brbank
  provider: one transaction per open installment is created and registered at
  the bank. *Generate boletos* again only issues the installments without a
  live title.
- If the bank is unavailable, the transaction stays in draft with the reason
  and the reconciliation cron registers it later with the same idempotency key.
  If the bank refuses the data, the posting stops with the reason, naming the
  missing customer fields.
- A title the bank has not confirmed yet (the Itaú Bolecode may answer "in
  progress") stays pending, takes no instruction and is not shown to the
  customer, until the reconciliation cron reads it as registered.
- The portal also offers the boleto PDF when the bank provides one.

Following up, in the transaction:

- *Check at the bank* reads the title back and applies its status. The
  *Capture* button of `payment` does the same, and *Void* writes the title off.
- *Bank instruction* sends a due date extension, a rebate or a protest; *Write
  off at the bank* cancels the title. The buttons only show when the bank
  declares the capability; a command the bank refuses stays recorded as
  rejected, with the reason.
- For BTG Pactual, the *Refresh Token* of the provider changes by itself after
  the calls to the bank: the provider keeps the last token the bank returned.
- *Invoicing > Customers > Boleto Instructions* lists every instruction, and
  *Invoicing > Configuration > Payments > Bank Webhook Events* every event
  received (managers only).

From the invoice: the *Receivables* tab has a *Bank instruction* button on each
open installment with a registered boleto, offering only what the bank accepts.
After the bank accepts:

- Due date extension: the due date of the installment and of the invoice change.
- Rebate: a credit note without taxes and without a fiscal document is posted on
  the *Rebate Account* of the provider and reconciled with the installment. If
  Odoo cannot post it, the instruction stays accepted, the reason goes to the
  invoice and an activity asks the salesperson (or the sender, when the
  salesperson has no access to invoices) to do it by hand.
- Write-off: the invoice only receives a message. The title remains open, since
  the customer still owes the amount.

Santander: a boleto the bank reports as written off, with no write-off sent from
Odoo, is not canceled: it may have been paid by Pix. The transaction stays open
with *Review Needed* filled, and the invoice receives a message and an activity.

Return files (CNAB): a module that reads a return file of an account that also
uses the API can call `payment.transaction._brbank_notify_cnab_occurrence(
nosso_numero, company)`: the transaction is found by its nosso numero and read
back from the bank, so the file and the API never settle the same title twice.
