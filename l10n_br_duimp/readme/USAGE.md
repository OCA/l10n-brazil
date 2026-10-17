**Search DUIMP (recommended)**

1. Go to *Accounting > Vendors > Search DUIMP*.
2. Pick a date range and click **Search**: every DUIMP registered for the
   company's CNPJ in that period is listed, except the ones already
   imported into Odoo.
3. Uncheck any DUIMP you do not want to import yet and click
   **Import Selected**.
4. A DUIMP import wizard, already queried, is opened for each selected
   DUIMP. Continue with steps 3-5 of *Import DUIMP (Manual)* below for
   each one.

**Import DUIMP (Manual)**

1. Go to *Accounting > Vendors > Import DUIMP (Manual)*.
2. Enter the DUIMP number (and optionally its version) and click
   **Query DUIMP**.
3. Review/adjust the grid, matching each DUIMP item to an internal
   product and CFOP.
4. If applicable, enter the **AFRMM Total** (not returned by the DUIMP
   query, taken from the DUIMP extract instead): it is allocated to each
   item proportionally to its customs value.
5. Click **Import** to generate the inbound fiscal document and the
   corresponding vendor bill.
6. The II, IPI, PIS and COFINS base/rate/amount fields are pre-filled
   with the values calculated in the DUIMP and remain freely editable on
   the generated invoice. ICMS is not returned by the DUIMP and must be
   filled in manually.
