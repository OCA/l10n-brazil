- `subscription_oca` creates one invoice per subscription, so lines that
  need different fiscal document types (goods and services together) are
  refused when the invoice is generated. Splitting the invoice per document
  type, as `l10n_br_sale` does, needs a grouping hook upstream.
- The *Sale order & Invoice* invoicing mode relies on `l10n_br_sale` to
  build the invoices from the generated order.
