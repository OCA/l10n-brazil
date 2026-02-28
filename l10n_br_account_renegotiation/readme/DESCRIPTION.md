This module allows renegotiating payment installments on posted invoices
without having to reset them to draft.

In Brazilian fiscal scenarios, it's common to need to adjust payment due
dates and amounts after an invoice (NFe) has been validated. This module
provides a wizard to modify the payment terms while keeping the fiscal
document unchanged.

Features:

  - Renegotiate payment installments on posted invoices
  - Modify due dates and amounts while keeping the total unchanged
  - Re-generate all installments from the payment term if needed
  - Edit the payment mode on installments (supports heterogenous payment modes)
  - Automatically logs changes in the invoice's chatter
  - Does not affect the fiscal document (NFe)
