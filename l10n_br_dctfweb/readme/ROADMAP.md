- The assessment reads only the tax assessments of its own company. A company
  with branches assesses IPI per establishment, and consolidating the branches
  into the assessment of the head office is not done yet: for now each debit
  carries the establishment of the company it was read from.
- IRPJ, CSLL and IOF are not covered by `l10n_br_tax_assessment`, so their
  debits are entered by hand. Reading them from the tax closing of `account`
  is the natural next step.
- The quota division of a quarterly IRPJ or CSLL debit is done in the DCTFWeb
  after the MIT is closed, and is not modelled here.
- The layout accepts a debit whose taxable fact happened after the last
  special event of the month. The flag exists on the debit, but nothing infers
  it from the date of the fact yet.
