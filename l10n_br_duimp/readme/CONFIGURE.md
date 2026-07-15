1. Register the e-CPF digital certificate of the person representing the
   company under *Accounting > Configuration > Certificates*
   (`l10n_br_fiscal_certificate` module) and link it under *Companies >
   (company) > E-CPF*. An e-CNPJ certificate is rejected by the Portal
   Único Siscomex for this profile (HTTP 422, code PLAT-ER2008).
2. Under *Companies > (company) > Fiscal Brazil*, set the Siscomex
   environment to use (Company Validation or Production).
