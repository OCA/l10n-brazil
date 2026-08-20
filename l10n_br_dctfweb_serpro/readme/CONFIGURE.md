Go to Settings > Companies > your company > DCTFWeb/MIT > Integra Contador.

**Environment.** Start on the trial, which is free and answers the same
services with test documents. Move to production only after the trial round
trip works.

**Credentials.** The consumer key and secret come from the Integra Contador
contract in the Serpro store. They are readable only by the system group: they
are the credential of the company at the tax authority.

**Certificate.** The requests go over mTLS with an e-CNPJ A1 certificate,
registered in the company through `l10n_br_fiscal_certificate`. An e-CPF is
not accepted by the platform.

**Accounting firm.** When the firm files for a client, fill in the contractor
CNPJ with the CNPJ of the firm and leave the taxpayer as the client company.
The client also has to grant the electronic power of attorney for the DCTFWeb
in the e-CAC; without it the platform answers a permission error, not a
validation one.

**Cost warning.** The platform bills per request, so every billed call asks
for confirmation before going out. Turn it off per company once the team knows
what it is doing.
