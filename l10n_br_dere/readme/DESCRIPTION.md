This module implements Wave 1 of the Brazilian **Declaração de Regimes
Específicos (DeRE)** layout **1.2.0**.

It lets an Odoo company:

- store the DeRE tax regime, activities and referential chart
- map `account.group` (synthetic) and `account.account` (analytic) PGCC fields
- keep D-1001 / D-1011 and the PGCC snapshot on a company table-validity
  period reused by monthly declarations
- generate local XML for D-1001, D-1011, D-1101, D-1106, D-1121, D-1198
  and D-1199
- send signed batches to Receita Integra, consult processing (manually or
  via cron with backoff) and store protocol, receipt and D-9xxx returns
- keep the RFB totals (D-9101 / D-9106 / D-9112), the D-9198 reopening
  return, the D-9199 IBS/CBS assessment and the D-9001 validity extract
  next to the local data, without posting a journal entry

It does **not** implement sector-specific rules (for example health-plan
premium vs administration-fee reconciliation). Those stay in company data or
in a dedicated extra addon.
