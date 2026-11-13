# Copyright (C) 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    coa_generic_tmpl = env.ref("l10n_br_coa_poppi.l10n_br_coa_poppi_chart_template")

    # Load COA for demo Company
    company_poppi = env.ref("l10n_br_coa_poppi.poppi_company", raise_if_not_found=False)
    if company_poppi:
        coa_generic_tmpl.try_loading(company=company_poppi)
        tools.convert_file(
            cr,
            "l10n_br_coa_poppi",
            "demo/account_journal.xml",
            None,
            mode="init",
            noupdate=True,
            kind="init",
        )
