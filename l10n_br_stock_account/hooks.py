# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_br_fiscal.tools import set_journal_in_fiscal_operation
from odoo.addons.l10n_br_stock.hooks import create_quants_for_inventory


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_l10n_br_stock_account").demo:
        create_quants_for_inventory(
            cr,
            [
                env.ref("stock.warehouse0").lot_stock_id,
                env.ref("l10n_br_stock.wh_empresa_simples_nacional").lot_stock_id,
                env.ref("l10n_br_stock.wh_empresa_lucro_presumido").lot_stock_id,
            ],
            [
                env.ref("product.product_product_12"),
                env.ref("product.product_product_16"),
            ],
        )

        # Load COA Fiscal Operation properties
        stock_account_set_journal_in_fiscal_operation(cr)


def stock_account_set_journal_in_fiscal_operation(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_l10n_br_stock_account").demo:
        # Load Fiscal Operation Main Company
        set_journal_in_fiscal_operation(
            cr,
            env.ref("base.main_company"),
            [
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_entrada_remessa",
                    "journal": "l10n_br_stock_account."
                    "entrada_remessa_journal_main_company",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_simples_remessa",
                    "journal": "l10n_br_stock_account."
                    "simples_remessa_journal_main_company",
                },
            ],
        )

        company_sn = env.ref(
            "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
        )

        set_journal_in_fiscal_operation(
            cr,
            company_sn,
            [
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_entrada_remessa",
                    "journal": "l10n_br_stock_account."
                    "entrada_remessa_journal_simples_nacional",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_simples_remessa",
                    "journal": "l10n_br_stock_account."
                    "simples_remessa_journal_simples_nacional",
                },
            ],
        )

        company_lc = env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        )

        set_journal_in_fiscal_operation(
            cr,
            company_lc,
            [
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_entrada_remessa",
                    "journal": "l10n_br_stock_account."
                    "entrada_remessa_journal_lucro_presumido",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_simples_remessa",
                    "journal": "l10n_br_stock_account."
                    "simples_remessa_journal_lucro_presumido",
                },
            ],
        )
