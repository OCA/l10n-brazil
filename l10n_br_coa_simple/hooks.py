# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    coa_simple_tmpl = env.ref("l10n_br_coa_simple.l10n_br_coa_simple_chart_template")
    if env["ir.module.module"].search_count(
        [
            ("name", "=", "l10n_br_account"),
            ("state", "=", "installed"),
        ]
    ):
        from odoo.addons.l10n_br_account.hooks import load_fiscal_taxes

        # Relate fiscal taxes to account taxes.
        load_fiscal_taxes(env, coa_simple_tmpl)

    # Load COA to Demo Company
    if not tools.config.get("without_demo"):
        user_admin = env.ref("base.user_admin")
        company = env.ref(
            "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
        )
        if company:
            user_admin.company_id = company
            coa_simple_tmpl.with_user(
                user=user_admin.id
            ).try_loading_for_current_company()

            tools.convert_file(
                cr,
                "l10n_br_coa_simple",
                "demo/account_journal.xml",
                None,
                mode="init",
                noupdate=True,
                kind="init",
                report=None,
            )

            user_admin.company_id = env.ref("base.main_company")
