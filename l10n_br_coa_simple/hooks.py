# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Load COA for demo Company
    company_sn = env.ref(
        "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
    )
    if company_sn:
        coa_simple_tmpl = env.ref(
            "l10n_br_coa_simple.l10n_br_coa_simple_chart_template"
        )
        coa_simple_tmpl.try_loading(company=company_sn)
        tools.convert_file(
            cr,
            "l10n_br_coa_simple",
            "demo/account_journal.xml",
            None,
            mode="init",
            noupdate=True,
            kind="init",
        )
