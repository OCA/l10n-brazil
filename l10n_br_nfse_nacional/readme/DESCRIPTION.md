This module issues the **national NFS-e** (electronic service invoice) directly
through the **Sefin Nacional / ADN** environment, with no paid gateway. From a
confirmed `l10n_br_fiscal.document` it builds the **DPS**, signs it with the
company ICP-Brasil A1 certificate, transmits it to the ADN over **REST/mTLS**
and stores the authorized NFS-e and its 50-digit access key.

It inherits `l10n_br_fiscal.document` directly and does **not** depend on
`l10n_br_nfse` (the municipal / ABRASF flow): all service and tax fields already
live in the fiscal core. See the project ADRs for the rationale.

The DPS data structure comes from `l10n_br_nfse_spec` (xsdata-odoo mixins over
the official v1.00 schemas), mapped onto the document via `spec_driven_model`.
