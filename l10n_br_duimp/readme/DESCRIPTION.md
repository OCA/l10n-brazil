Queries the DUIMP (Import Declaration) directly from the Portal Único
Siscomex REST API, authenticating with the e-CPF digital certificate of
the person representing the company (the Siscomex Plataforma auth module
rejects e-CNPJ for this profile), and uses the returned data (items,
customs values, and federal taxes already calculated by the customs
broker/Siscomex - II, IPI, PIS, COFINS) to automatically generate an
inbound fiscal document and the corresponding vendor bill.

Since the DUIMP does not provide ICMS (a state tax) and its values do not
always match exactly what must be booked, every tax base/amount field
remains freely editable after the import.
