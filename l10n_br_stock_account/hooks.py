# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):

    if not tools.config["without_demo"]:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Load COA Fiscal Operation properties
        company = env.ref(
            "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
        )
        # COA Simple Fiscal Operation properties
        if company and env["ir.module.module"].search_count(
            [
                ("name", "=", "l10n_br_coa_simple"),
                ("state", "=", "installed"),
            ]
        ):
            tools.convert_file(
                cr,
                "l10n_br_stock_account",
                "demo/fiscal_operation_simple.xml",
                None,
                mode="init",
                noupdate=True,
                kind="init",
                report=None,
            )

        company_lc = env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        )

        # COA Generic Fiscal Operation properties
        if company_lc and env["ir.module.module"].search_count(
            [
                ("name", "=", "l10n_br_coa_generic"),
                ("state", "=", "installed"),
            ]
        ):
            tools.convert_file(
                cr,
                "l10n_br_stock_account",
                "demo/fiscal_operation_generic.xml",
                None,
                mode="init",
                noupdate=True,
                kind="init",
                report=None,
            )
