In **Match with Orders** of an imported document, the lines of approved purchase
requests (or in progress) that have a balance without order appear next to the
lines of the document, with the person who requested, the date and the
quantity. A request of a product with a preferred supplier shows for the
document of that supplier only; one without preferred supplier shows for any.

A purchase request is not a commitment to the supplier, so **Match** refuses it.
Select the document lines and one request line and press **Create Order from
Request**:

- the order is created by the purchase request wizard, with the supplier of the
  document, the quantity and the price of the document lines (the quantity is
  the one of the document even when it is higher than the request), and it is
  confirmed;
- when the company asks for approval of the order, it stays waiting and the
  document lines are only suggested for it, so the invoice is not generated
  before the approval; when the order is confirmed the lines are resolved;
- the document line keeps the request line it came from, and the request shows
  the order.

A unit the supplier declared and nobody confirmed is not converted silently: the
action asks to choose the unit on the line first. A line without product takes
the product of the request line.
