# Copyright (C) 2026 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

OLD_COLUMNS = {
    "danfe_invoice_display": "invoice_display",
    "danfe_display_pis_cofins": "display_pis_cofins",
    "danfe_margin_top": "margin_top",
    "danfe_margin_right": "margin_right",
    "danfe_margin_bottom": "margin_bottom",
    "danfe_margin_left": "margin_left",
}


@openupgrade.migrate()
def migrate(env, version):
    """Move the DANFE options from res_company to DANFE profiles.

    Companies with the default options share the default profile; each other
    set of options becomes a profile of its own, named after the first company
    using it.

    This runs as a post script because the l10n_br_nfe_danfe_profile table and
    its default record only exist after the module is loaded.
    """
    if not openupgrade.column_exists(env.cr, "res_company", "danfe_margin_top"):
        return

    profile_model = env["l10n_br_nfe.danfe.profile"]
    default_profile = env.ref("l10n_br_nfe.danfe_profile_default")
    defaults = profile_model.default_get(list(OLD_COLUMNS.values()))
    default_values = {
        field_name: defaults.get(field_name, False)
        for field_name in OLD_COLUMNS.values()
    }

    openupgrade.logged_query(
        env.cr,
        """
        SELECT
            id,
            danfe_invoice_display,
            danfe_display_pis_cofins,
            danfe_margin_top,
            danfe_margin_right,
            danfe_margin_bottom,
            danfe_margin_left
        FROM res_company
        ORDER BY id
        """,
    )
    profiles = {}
    for company_id, *old_values in env.cr.fetchall():
        values = {
            field_name: default_values[field_name] if value is None else value
            for field_name, value in zip(OLD_COLUMNS.values(), old_values, strict=True)
        }
        key = tuple(values.items())
        if key not in profiles:
            if values == default_values:
                profiles[key] = default_profile
            else:
                company = env["res.company"].browse(company_id)
                profiles[key] = profile_model.create(dict(values, name=company.name))
        env["res.company"].browse(company_id).danfe_profile_id = profiles[key]

    openupgrade.drop_columns(
        env.cr, [("res_company", column) for column in OLD_COLUMNS]
    )
