- Inherit `l10n_br_dere_spec` mixins on the concrete records and drop the
  parallel snake_case fields (`c_cta`, `v_apur`, …). Map Odoo data into
  `dere12_*` (ECD-style `_map_from_odoo`), then generate XML from those
  fields. Do not introduce `spec_driven_model.StackedModel` until a xsdata
  binding exists for DeRE (same role nfelib plays for NF-e / CT-e / MDF-e).
- Send D-1198 reopening to Receita Integra
- Full D-1106 and D-1121 business rules
- Transactional events (D-3201 and remaining D-22xx / D-32xx) after CGIBS
  publishes a stable transactional layout
