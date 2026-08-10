This module issues the **national NFS-e** (electronic service invoice) directly
through the **Sefin Nacional / ADN** environment, with no paid gateway. From a
confirmed `l10n_br_fiscal.document` it builds the **DPS**, signs it with the
company ICP-Brasil A1 certificate, transmits it to the ADN over **REST/mTLS**
and stores the authorized NFS-e and its 50-digit access key.

It builds on `l10n_br_nfse` for the NFS-e provider and environment settings, but
maps the DPS straight onto `l10n_br_fiscal.document`: all service and tax fields
already live in the fiscal core, so nothing of the municipal / ABRASF flow is
reused.

The DPS data structure comes from `l10n_br_nfse_spec` (xsdata-odoo mixins over
the official v1.00 schemas), mapped onto the document via `spec_driven_model`.
