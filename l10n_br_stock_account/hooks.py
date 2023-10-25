# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):
    cr.execute("select demo from ir_module_module where name='l10n_br_stock_account';")
    if cr.fetchone()[0]:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Load COA Fiscal Operation properties
        company = env.ref(
            "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
        )

        # Caso o modulo l10n_br_purcase ou l10n_br_sale esteja instalado,
        # o que acontece na forma que o Travis faz os testes, acontece o
        # erro abaixo:
        #   File "/odoo/src/odoo/sql_db.py", line 300, in execute
        #     res = self._obj.execute(query, params)
        # psycopg2.IntegrityError: duplicate key value violates
        # unique constraint "ir_property_unique_index"
        # DETAIL:  Key (fields_id, COALESCE(company_id, 0),
        # COALESCE(res_id, ''::character varying))=(13446, 1,
        # l10n_br_fiscal.operation,6) already exists.
        # TODO: teria uma solução melhor?
        l10n_br_sale_or_purchase_installed = False
        if env["ir.module.module"].search_count(
            [
                ("name", "=", "l10n_br_purchase"),
                ("state", "=", "installed"),
            ]
        ) or env["ir.module.module"].search_count(
            [
                ("name", "=", "l10n_br_sale"),
                ("state", "=", "installed"),
            ]
        ):
            l10n_br_sale_or_purchase_installed = True

        # COA Simple Fiscal Operation properties
        if company and env["ir.module.module"].search_count(
            [
                ("name", "=", "l10n_br_coa_simple"),
                ("state", "=", "installed"),
            ]
        ):
            if not l10n_br_sale_or_purchase_installed:
                tools.convert_file(
                    cr,
                    "l10n_br_stock_account",
                    "demo/fiscal_operation_simple.xml",
                    None,
                    mode="init",
                    noupdate=True,
                    kind="init",
                )
            else:
                env.ref("l10n_br_fiscal.fo_simples_remessa")
                data_op_fiscal = "l10n_br_fiscal.operation," + str(
                    env.ref("l10n_br_fiscal.fo_simples_remessa").id
                )
                main_company = env.ref("base.main_company", raise_if_not_found=False)
                simples_remessa_main_company = env["ir.property"].search(
                    [
                        ("res_id", "=", data_op_fiscal),
                        ("company_id", "=", main_company.id),
                    ]
                )

                data_journal = "account.journal," + str(
                    env.ref(
                        "l10n_br_stock_account.simples_remessa_journal_main_company"
                    ).id
                )
                simples_remessa_main_company.value_reference = data_journal

                # Devolução de Vendas
                data_op_fiscal = "l10n_br_fiscal.operation," + str(
                    env.ref("l10n_br_fiscal.fo_devolucao_venda").id
                )
                devolucao_vendas_main_company = env["ir.property"].search(
                    [
                        ("res_id", "=", data_op_fiscal),
                        ("company_id", "=", main_company.id),
                    ]
                )
                data_journal = "account.journal," + str(
                    env.ref(
                        "l10n_br_stock_account.devolucao_vendas_journal_main_company"
                    ).id
                )
                devolucao_vendas_main_company.value_reference = data_journal

                # Devolução de Compras
                data_op_fiscal = "l10n_br_fiscal.operation," + str(
                    env.ref("l10n_br_fiscal.fo_devolucao_compras").id
                )
                devolucao_compras_main_company = env["ir.property"].search(
                    [
                        ("res_id", "=", data_op_fiscal),
                        ("company_id", "=", main_company.id),
                    ]
                )
                data_journal = "account.journal," + str(
                    env.ref(
                        "l10n_br_stock_account.devolucao_compras_journal_main_company"
                    ).id
                )
                devolucao_compras_main_company.value_reference = data_journal

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
            if not l10n_br_sale_or_purchase_installed:
                tools.convert_file(
                    cr,
                    "l10n_br_stock_account",
                    "demo/fiscal_operation_generic.xml",
                    None,
                    mode="init",
                    noupdate=True,
                    kind="init",
                )
            else:
                data_op_fiscal = "l10n_br_fiscal.operation," + str(
                    env.ref("l10n_br_fiscal.fo_simples_remessa").id
                )
                simples_remessa_company_lc = env["ir.property"].search(
                    [
                        ("res_id", "=", data_op_fiscal),
                        ("company_id", "=", company_lc.id),
                    ]
                )

                data_journal = "account.journal," + str(
                    env.ref(
                        "l10n_br_stock_account.simples_remessa_journal_lucro_presumido"
                    ).id
                )

                simples_remessa_company_lc.value_reference = data_journal
