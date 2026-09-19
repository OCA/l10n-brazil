Install this module only as a dependency of `l10n_br_dere`.

Field names use the `dere12_` prefix (layout 1.2.x). A later major layout
would introduce a new prefix, following the same convention used by
`l10n_br_nfe_spec`.

Wave 1 mixins under `models/v1_2/` are the curated flat abstracts used by
`l10n_br_dere` (`dere.12.infoconta`, `dere.12.balanceteconta`, …). Do not
replace them with a raw `xsdata-odoo` dump until the official `DeRE` root
is namespaced per event (see ROADMAP).
