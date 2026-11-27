When the origin of a line is decided, the line also points to the receipt move
of the order line if there is a single candidate: the received and not yet
invoiced move first, otherwise the only one still to come. Returns are never
candidates.

In **Match with Orders** the receipts appear as lines of their own, to receive
or received. Select the document line, the order line and one of its receipts
and press **Match** to choose the receipt. Other buttons:

- **Open Receipt**: opens the receipt of the selected lines with the quantity
  of the document, and the lots and expiry dates the document declares for products
  tracked by lot, proposed. A move that already has lots or quantities is not
  changed, and nothing is validated.
- **Create Receipt**: for a line of a stockable product marked as without
  order, creates an incoming receipt in the warehouse of the company, confirmed
  and not validated, and links it to the line.
- **No Stock Entry**: only a purchase manager or a stock manager can mark that
  the goods of a line without order do not enter the stock.

**Generate Invoice** refuses a line of a stockable product marked as without
order that has no receipt and is not marked as without stock entry.

On a receipt linked to a document with lots, **Propose Lots from the Document** fills
the lots, quantities and expiry dates. Several lots for one item are supported;
a product without lot tracking is ignored; a receipt that already has lots or
quantities is kept. The expiry date is written when `product_expiry` is
installed.

The lines of the document and of the bill show the ordered and received
quantity, the order price and the differences. A line out of the tolerances of
the company (Bill Price Tolerance and Bill Quantity Tolerance, in percentage,
zero by default) is marked as divergent, the document and the bill get a badge,
and the lists have a filter. A bill issued before the receipt stays divergent
until the goods are received.
