- Migrate `xml_builder` to [derelib](https://github.com/Escodoo/derelib)
  (xsdata binding for DeRE 1.2.0, same role nfelib plays for NF-e /
  CT-e / MDF-e): build, sign, batch and parse returns through the
  library, keeping business rules (`tpOper`, MS1135 / MS1147, PGCC
  checks) in this module. Do not introduce
  `spec_driven_model.StackedModel` before that migration.
- Do not inherit event mixins (D-1001 / D-1011 / D-1101 / D-1199) on
  `l10n_br_dere.declaration`, `l10n_br_dere.table.period` or
  `l10n_br_dere.event`: those abstracts share `dere12_id` and `dere12_tpOper`.
- Official `tpOper` 1/2/3 (and D-1121 `4` after the first D-1199) is
  implemented. D-1198 / D-1199 stay inclusion-only.
- D-1121 `infoImovel` and D-1021 (required before `motExcl` 1)
- Local replica of MS1155 (future `perApur`): the official rule does not
  interrupt processing, and the test suite uses future months
- Transactional events (D-3201 and remaining D-22xx / D-32xx) after CGIBS
  publishes a stable transactional layout
- D-9199 content not stored yet: `gCoeficientes` (financial services and
  prize contests) and the `infoBCN` / `detBCN` breakdown of the negative
  base carried forward per origin. Only the final negative balances are
  kept on the assessment lines.
- D-9121 (public-bond operations) and D-9209 (transactional) returns are
  recognized and validated, but their content is not applied until the
  matching events are implemented.
- Optional journal entry for the IBS / CBS assessed by D-9199; today the
  amounts are recorded for reference only.
- D-1199 `gUtilizBCN` (negative-base recovery). The group is optional
  (`usarBCNAcum` / `metodoAproveit` / `detBCNeg`). Official Tabela 12
  (`codBC` / `codBCNRaiz`) belongs with that feature, not as a standalone
  catalog today: D-9199 already returns `xDetBC` on each assessment line.
- D-2101 (public-bond titles) is out of scope for health-plan operators.
- Consult backoff has no max attempt count (manual Dev §3.3). Delay is
  capped at 60 minutes and the batch stays `sent` until a result arrives.
- Official Anexo I tables that stay out of this module on purpose:
  - 13 / 15 reuse `res.country.state` / `res.country`
  - 14 / 22 / 23 / 24 / 32 are external referential charts (SPED, COSIF,
    SUSEP, PREVIC, ANS). They belong in a chart-of-accounts addon, not
    here. MS1077 (account missing from the official chart) stays
    server-side.
  - 33 (health-premium age coefficients) belongs with D-3201
- MS1114 (`cCtaRef` of a split account must match the parent) is only a
  warning at the RFB and is not replicated locally.
