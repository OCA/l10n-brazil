- The transmission of the file is not automated: the file must be validated
  and transmitted with the SEFAZ *Validador/Transmissor* application, which
  is a Windows desktop program (there is no web service for the FCI).
- The FCI control number is not yet written in the NF-e: the field `nFCI`
  (group I07 of the NF-e layout) is still a TODO of the `l10n_br_nfe`
  module.
- The goods lines are not filled in automatically from the fiscal documents
  of the period, the amounts must be informed by the user.
