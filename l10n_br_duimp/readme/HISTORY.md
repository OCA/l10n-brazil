## 16.0.1.0.0 (2026-07-08)

- First version (Escodoo): query the DUIMP through the Portal Único
  Siscomex API and generate the fiscal document / vendor bill.
- "Search DUIMP" wizard: lists every DUIMP registered for the company's
  CNPJ in a date range (Portal Único
  `/ext/duimp/chaves-acesso/importadores/{ni}`), excludes the ones
  already imported into Odoo, and lets the user multi-select which ones
  to import, so the DUIMP number no longer has to be typed manually.
- Persistent DUIMP (KMEE, merging the `l10n_br_di` 14.0 data model): the
  DUIMP becomes a first-class object (`l10n_br_duimp.declaracao`) with
  items, per-item federal taxes, additions/deductions, payments, a state
  machine and chatter; the import wizard creates/refreshes it instead of
  a transient grid; product auto-match by `codigoProduto`/NCM; cost
  allocation (AFRMM / Siscomex fee / capatazia by customs value) and
  implicit exchange rates ported from the DI; NF-e `nfe40_DI`/`adi` tags
  provided by the companion module `l10n_br_duimp_nfe`.
