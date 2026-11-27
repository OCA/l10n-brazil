Link between the import of fiscal documents (`l10n_br_fiscal_edi`), the
purchase link (`l10n_br_purchase_edi`) and stock
(`l10n_br_purchase_stock`). It installs itself when they are present.

- The receipt move is the origin of an imported document line, together with
  the purchase order line, and appears in the reconciliation screen as a
  source of its own.
- A stockable product bought without an order can have the receipt created from
  the document.
- The lots and expiry dates the document declares (`_edi_get_lots` of its
  line, whatever the type of the document) are proposed on the receipt for the
  operator to review.
- The document line and the bill line are compared with the order and the
  receipt: ordered, received and invoiced quantities, order price, and the
  differences, with tolerances by company. It only warns, nothing is blocked.
