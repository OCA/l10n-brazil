Persists the DUIMP (Declaração Única de Importação) as a first-class
object in Odoo and generates the inbound fiscal document and vendor bill
from it.

It queries the DUIMP directly from the Portal Único Siscomex REST API,
authenticating with the e-CPF digital certificate of the person
representing the company (the Siscomex Plataforma auth module rejects
e-CNPJ for this profile), and stores the returned data as persistent,
auditable records: the declaration header, its items (with the internal
product/CFOP matching), the federal taxes calculated per item (II, IPI,
PIS, COFINS), the additions/deductions, the exchange rates and the
payments. From those records it generates the inbound fiscal document
and the corresponding vendor bill.

This module merges the persistent data model of KMEE's `l10n_br_di`
(Declaração de Importação, Odoo 14.0) with the Portal Único API client
contributed by Escodoo, targeting the migration from DI to DUIMP.

Since the DUIMP does not provide ICMS (a state tax) and its values do not
always match exactly what must be booked, every tax base/amount field
remains freely editable on the generated invoice.

The NF-e import-declaration tags (`nfe40_DI`/`adi`) for re-issuing an
inbound NF-e are provided by the companion module `l10n_br_duimp_nfe`.
