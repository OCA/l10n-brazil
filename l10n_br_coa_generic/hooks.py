# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    coa_generic_tmpl = env.ref("l10n_br_coa_generic.l10n_br_coa_generic_template")

    # Load COA for demo Company
    company_lc = env.ref(
        "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
    )
    if company_lc:
        coa_generic_tmpl.try_loading(company=company_lc)
        tools.convert_file(
            cr,
            "l10n_br_coa_generic",
            "demo/account_journal.xml",
            None,
            mode="init",
            noupdate=True,
            kind="init",
        )
