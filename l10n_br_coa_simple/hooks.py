# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import tools


def post_init_hook(env):
    # Load COA for SN Company
    company_sn = env.ref(
        "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
    )
    if company_sn:
        chart_template = env["account.chart.template"]
        chart_template.try_loading("br_oca_simple", company_sn, install_demo=True)
        tools.convert_file(
            env,
            "l10n_br_coa_simple",
            "demo/account_journal.xml",
            None,
            mode="init",
            noupdate=True,
            kind="init",
        )
