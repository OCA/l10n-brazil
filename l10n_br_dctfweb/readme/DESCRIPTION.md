This module assesses the federal debits of the MIT, the tax inclusion module
that feeds the DCTFWeb, and builds the JSON file the authority imports.

Since January 2025 the DCTF PGD no longer exists: the debits of IRPJ, CSLL,
PIS/Pasep, COFINS, IPI, IOF, CIDE, CONDECINE, CPSS and the unified payment are
confessed in the monthly DCTFWeb through the MIT (IN RFB 2.237/2024, art. 9).
Withholdings and the contribution on payroll stay out: they belong to the
EFD-Reinf and to the eSocial, which are generating bookkeeping of their own.

The module does not compute a single tax. It reads the assessment that
`l10n_br_tax_assessment` already persisted, the same one the EFD Contribuicoes
and the EFD ICMS/IPI read, and turns it into a confession. That is the point:
the escrituracao, the books and the confession come from one number, so they
cannot diverge and produce a fine later.

What it does:

- reads the persisted assessments of the period and writes one debit per
  revenue code, keeping the trail back to the assessment it came from;
- carries the whole official revenue code table, 240 codes, each one with the
  attributes the layout demands of it;
- checks the pendencies the authority's own application checks before letting
  an assessment be closed;
- builds the JSON of layout 1.0 (ADE CORAT 19/2024, rectified on 2025-02-20),
  including special events, suspensions and the assessment without movement;
- names the file the way the layout requires, so it can be imported as it is.

Transmission is not here. It lives in `l10n_br_dctfweb_serpro`, so a company
that only wants the file to import in the e-CAC does not have to install a
transmission stack it will never use.
