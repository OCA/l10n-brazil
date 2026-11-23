- Receipts (stock) and purchase requests as sources of the reconciliation: each
  module adds its `SELECT` to `_match_sources` of
  `l10n_br_purchase_edi.match`, with the next source type of the ids.
- A separate strip of weaker candidates (same product, supplier different or
  not defined) for purchases made outside the system.
- A menu with the pending documents grouped by supplier.
- The tolerance of the ordered quantity (`_import_quantity_tolerance`) is zero
  here; the stock link may extend it.
- A bill that already exists is not changed when the origin is decided later.
