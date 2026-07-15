## 16.0.1.0.0 (2026-07-08)

- First version: query the DUIMP through the Portal Único Siscomex API
  and generate the fiscal document / vendor bill.
- "Search DUIMP" wizard: lists every DUIMP registered for the company's
  CNPJ in a date range (Portal Único
  `/ext/duimp/chaves-acesso/importadores/{ni}`), excludes the ones
  already imported into Odoo, and lets the user multi-select which ones
  to import, so the DUIMP number no longer has to be typed manually.
