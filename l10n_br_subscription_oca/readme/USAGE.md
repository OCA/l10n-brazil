1. Create a subscription as usual. For Brazilian companies the form shows
   the *Fiscal Operation* (defaulting to the company sale fiscal operation),
   the final consumer and presence indicators, and the lines show the
   *Operation Line* and the *Fiscal Taxes* instead of the account taxes.
2. Users of the *Line fiscal detail* group (from `l10n_br_sale`) open each
   line in a form with the full fiscal detail (taxes, amounts, extra info).
3. Generate the invoice (*Create Invoice* button, start of the subscription
   or the recurring cron): it is created with the fiscal document type and
   serie of the lines and can be issued like any other Brazilian invoice.

All lines of a subscription must share the same fiscal document type:
keep goods (NF-e) and services (NFS-e) in separate subscriptions.
