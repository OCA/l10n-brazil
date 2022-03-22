# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):

    if not tools.config["without_demo"]:
        env = api.Environment(cr, SUPERUSER_ID, {})
        purchase_orders = env["purchase.order"].search(
            [("company_id", "!=", env.ref("base.main_company").id)]
        )

        for order in purchase_orders:
            defaults = order.with_context(company_id=order.company_id.id).default_get(
                order._fields
            )
            defaults.update(
                {
                    "name": order.name,
                    "company_id": order.company_id.id,
                    "fiscal_operation_id": order.fiscal_operation_id.id,
                }
            )
            order.write(defaults)

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
                "l10n_br_purchase",
                "demo/fiscal_operation_simple.xml",
                None,
                mode="init",
                noupdate=True,
                kind="init",
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
                "l10n_br_purchase",
                "demo/fiscal_operation_generic.xml",
                None,
                mode="init",
                noupdate=True,
                kind="init",
            )
