This module implements Wave 1 of the Brazilian **Declaração de Regimes
Específicos (DeRE)** layout **1.2.0**.

It lets an Odoo company:

- store the DeRE tax regime, activities and referential chart
- map `account.account` lines to PGCC fields (`cCtaRef`, `codTrib`, `codNat`)
- generate local XML for D-1001, D-1011, D-1101, D-1198 and D-1199
- send signed batches to Receita Integra, consult processing (manually or
  via cron) and store protocol, receipt and D-9xxx returns

It does **not** implement sector-specific rules (for example health-plan
premium vs administration-fee reconciliation). Those stay in company data or
in a dedicated extra addon.
