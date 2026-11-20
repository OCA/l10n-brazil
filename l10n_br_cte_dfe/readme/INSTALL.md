Dependências:

1. **Módulos Odoo:** `l10n_br_fiscal_dfe` e `l10n_br_cte`.
2. **Bibliotecas Python:**
    * `nfelib` (>= 3.3.0): bindings e cliente SOAP `nfelib.cte.client.v4_0.dfe.DfeClient`.
    * `brazil_fiscal_client`: transporte SOAP com certificado A1.
    * `brazilfiscalreport`: geração do DACTE em PDF.

```bash
pip install nfelib brazil-fiscal-client brazilfiscalreport
```

A empresa precisa de UF, CNPJ e **certificado digital A1** válidos (módulo `l10n_br_fiscal_certificate`).
