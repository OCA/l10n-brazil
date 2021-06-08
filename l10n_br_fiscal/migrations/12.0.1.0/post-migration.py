# Copyright (C) 2021 - TODAY Raphael Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

from odoo.addons.l10n_br_fiscal.hooks import post_init_hook


@openupgrade.migrate()
def migrate(env, version):
    post_init_hook(env.cr, None)

    # if not coming from a v10 database return
    if not openupgrade.table_exists(
        env.cr, "l10n_br_fiscal_document_invalidate_number"
    ):
        return

    # else migrate some partner fiscal data:
    env.cr.execute(
        """
        SELECT id, code, is_company FROM l10n_br_account_partner_fiscal_type;
        """
    )
    fiscal_profiles = env.cr.fetchall()
    for profile in fiscal_profiles:
        code = False
        if profile[1] == "Contribuinte":
            code = "CNT"
        if profile[1] == "Simples Nacional":
            code = "SNC"
        if profile[1] == "Não Contribuinte" and profile[2]:
            code = "CNT"
        if profile[1] == "Não Contribuinte" and not profile[2]:
            code = "PFNC"
        # TODO map Revenda?
        if code:
            openupgrade.logged_query(
                env.cr,
                """
                UPDATE res_partner set fiscal_profile_id=
                (SELECT id from l10n_br_fiscal_partner_profile
                WHERE code=%s)
                WHERE openupgrade_legacy_12_0_partner_fiscal_type_id=%s
                """,
                (code, profile[0]),
            )

    # and then migrate product fiscal data:
    env.cr.execute(
        """SELECT product_template.id, c.code FROM product_template
        JOIN account_product_fiscal_classification as c
        ON c.id = openupgrade_legacy_12_0_fiscal_classification_id
        WHERE c.code IS NOT NULL;
        """
    )
    templates = env.cr.fetchall()
    for item in templates:
        tmpl = env["product.template"].browse(item[0])
        ncms = env["l10n_br_fiscal.ncm"].search([("code", "=", item[1])])
        product_data = {}
        if ncms:
            product_data["ncm_id"] = ncms[0].id
        genre_code = item[1][0:2]
        genres = env["l10n_br_fiscal.product.genre"].search([("code", "=", genre_code)])
        if genres:
            product_data["fiscal_genre_id"] = genres[0].id
        if ncms or genres:
            tmpl.write(product_data)
