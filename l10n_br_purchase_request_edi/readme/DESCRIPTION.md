Link between the import of fiscal documents (`l10n_br_fiscal_edi`), the
purchase link (`l10n_br_purchase_edi`) and the purchase requests
(`l10n_br_purchase_request`). It installs itself when they are present.

A vendor document with no purchase order may still have been asked for by
someone. The lines of approved purchase requests that have a quantity still
without order appear in the reconciliation screen as a source of their own, with
who requested, the date and the quantity. From there the order of the request is
created with the supplier, quantity and price of the document and the document
lines are matched to it, leaving the trace request, order and document.
