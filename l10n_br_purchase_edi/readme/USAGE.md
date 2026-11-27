After importing a vendor NF-e, the lines of the document show an origin
column.

- When the supplier declared the order and the item in the file and exactly one
  open order line has the product, the origin is resolved by itself.
- When the supplier has a single open order line for the product, the origin is
  suggested. Press **Confirm Origins** on the document to accept the
  suggestions.
- When there are several candidates, the origin stays pending and the line
  form lets you choose the order line.

**Generate Invoice** refuses the document while a line has a suggested origin
or a pending one with candidates. The bill links each line to its order line,
fills the source document with the order number, and the order shows the
invoiced quantity.

**Match with Orders** opens the reconciliation of the document: its lines, the
confirmed order lines with their balance and the quotations of the supplier.
Select the document lines and one order line and press **Match**. Other
buttons:

- **Undo**: the origin goes back to pending.
- **Without Order**: records that there is no order, with who did it and when.
- **Open Quotation**: opens the quotation so the buyer confirms it. A quotation
  cannot be matched; once the order is confirmed the line receives the
  suggestion.
- **Create Order from the Document**: creates a draft purchase order with the
  selected lines (supplier, product, quantity and price of the document). It is
  not confirmed; when the buyer confirms it, the line receives the suggestion.
