- The IBSCBS group falls back to fixed values (CST 000, cClassTrib 000001,
  cIndOp 050101) when the line carries no RTC data; fill the line RTC data to
  have it exported by `l10n_br_nfse_nacional` instead.
- The 9-digit municipal taxation code of Goiânia is injected after the
  national serialization, because the national XSD accepts only 3 digits; the
  DPS is validated against the national XSD, not the NotaControl
  `schema_v101.xsd`.
- Cancellation through the e101103 event of the NotaControl sample; the base
  module builds e101101.
- Confirm the signature algorithm in the homologation environment.
