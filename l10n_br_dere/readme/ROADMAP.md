- Keep `xml_builder` until a xsdata binding exists for DeRE (same role nfelib
  plays for NF-e / CT-e / MDF-e). Do not introduce
  `spec_driven_model.StackedModel` before that binding.
- Do not inherit event mixins (D-1001 / D-1011 / D-1101 / D-1199) on
  `l10n_br_dere.declaration` or `l10n_br_dere.event`: those abstracts share
  `dere12_id` and `dere12_tpOper`.
- Full D-1106 and D-1121 business rules
- Transactional events (D-3201 and remaining D-22xx / D-32xx) after CGIBS
  publishes a stable transactional layout
