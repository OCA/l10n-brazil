**Search DUIMP (recommended)**

1. Go to *Accounting > Vendors > Search DUIMP*.
2. Pick a date range and click **Search**: every DUIMP registered for the
   company's CNPJ in that period is listed, except the ones already
   imported into Odoo.
3. Uncheck any DUIMP you do not want to import yet and click
   **Import Selected**: a persistent DUIMP record is created for each
   selected one, already populated from the Portal Único. Continue with
   steps 3-6 of *Query DUIMP (Manual)* below for each one.

**Query DUIMP (Manual)**

1. Go to *Accounting > Vendors > Query DUIMP*.
2. Enter the DUIMP number (and optionally its version), the import fiscal
   operation and, if known from the DUIMP extract, the AFRMM / Siscomex
   fee / capatazia totals, then click **Query DUIMP**.
3. A persistent DUIMP record is created and opened. On the *Items* tab,
   match each item to an internal product and CFOP (products are
   auto-matched by the DUIMP `codigoProduto` / NCM when possible).
4. Set the vendor and review the costs and taxes on the *Costs & Taxes*
   tab. You can re-query the Siscomex at any time with **Refresh from
   Siscomex** while the DUIMP is not yet invoiced.
5. Click **Generate Vendor Bill** to create the inbound fiscal document
   and the corresponding vendor bill. The DUIMP is then locked.
6. The II, IPI, PIS and COFINS base/rate/amount fields are pre-filled
   with the values calculated in the DUIMP (per item when the payload
   provides the breakdown, otherwise allocated from the header totals by
   customs value) and remain freely editable on the generated invoice.
   ICMS is not returned by the DUIMP and must be filled in manually.
