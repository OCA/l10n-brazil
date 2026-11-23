- The receipt created from a document uses the price of the document as cost;
  the net cost without the recoverable taxes (`stock_cost_unit`) is not
  proposed yet.
- The divergence is not stored, so the filters of the lists read the lines
  linked to an order line; measure it on a large database before storing and
  indexing it.
- The receipt of a line decided as without order is not taken back if the
  decision is changed afterwards.
