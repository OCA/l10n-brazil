Go to _Settings > Companies_, open the company and use the **Assisted Assessment** tab:

- **Subject to DeRE**: enable it for taxpayers required to file the Specific Regimes
  Declaration. The assessment is then presented by the 20th instead of the 15th of the
  following month.
- **Assessment Calendar**: the calendar holding the national, state and municipal
  holidays of the head office domicile, used to find the last business day of the
  deadline. Without a calendar only weekends are skipped. Holidays can be loaded with
  the wizard provided by `l10n_br_resource`.
- **Reconciliation Tolerance**: absolute difference below which a line is considered
  reconciled. Defaults to one cent.

Holidays added to the calendar after an assessment has been created do not recompute its
deadline. Save the assessment again to refresh it.
