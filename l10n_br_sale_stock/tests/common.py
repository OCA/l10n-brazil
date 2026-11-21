# Copyright (C) 2026-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon
from odoo.addons.l10n_br_stock_account.tests.tools import (
    create_br_journal_and_set_fiscal_ops,
)
from odoo.addons.sale_stock_picking_invoicing.tests.common import (
    TestSaleStockPickingInvoicingCommon,
)
from odoo.addons.sale_stock_picking_invoicing.tests.tools import (
    create_with_form_sale_order,
)


@tagged("post_install", "-at_install")
class TestBRSaleStockPckInvCommon(
    TestSaleStockPickingInvoicingCommon, TestBrPickingInvoicingCommon
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        create_br_journal_and_set_fiscal_ops(
            cls.env, cls.env.company, cls.env.ref("l10n_br_fiscal.fo_venda")
        )

        # Check field analytic_distribution
        analytic_plan = cls.env["account.analytic.plan"].create(
            {
                "name": "default",
                "applicability_ids": [
                    Command.create(
                        {
                            "business_domain": "bill",
                            "applicability": "optional",
                        }
                    )
                ],
            }
        )
        analytic_account = cls.env["account.analytic.account"].create(
            {"name": "default", "plan_id": analytic_plan.id}
        )
        cls.env["account.analytic.distribution.model"].create(
            {
                "product_id": cls.product_storable_1.id,
                "analytic_distribution": {str(analytic_account.id): 100},
                "company_id": cls.env.company.id,
            }
        )
        # Segunda Plano/Conta Analítica para os casos com mais de um Plano
        analytic_plan_2 = cls.env["account.analytic.plan"].create({"name": "Plan Test"})
        cls.env["account.analytic.account"].create(
            {"name": "manual", "plan_id": analytic_plan_2.id}
        )

        cls.sale_order_br_1 = cls._create_br_sale_order(
            cls.partner_br_stock_1,
            cls.partner_br_stock_1,
            cls.partner_br_stock_1,
            cls.so_line_product_1
            + cls.so_line_note
            + cls.so_line_section
            + cls.so_line_product_2,
        )

        cls.sale_order_br_2 = cls._create_br_sale_order(
            cls.partner_br_stock_1,
            cls.partner_br_stock_1,
            cls.partner_br_stock_1,
            cls.so_line_product_1
            + cls.so_line_note
            + cls.so_line_section
            + cls.so_line_product_2,
        )

        cls.sale_order_br_3 = cls._create_br_sale_order(
            cls.partner_br_stock_1,
            cls.partner_br_stock_1_delivery_address,
            cls.partner_br_stock_1,
            cls.so_line_product_1
            + cls.so_line_note
            + cls.so_line_section
            + cls.so_line_product_service,
        )

        cls.sale_order_br_4 = cls._create_br_sale_order(
            cls.partner_br_stock_1_delivery_address,
            cls.partner_br_stock_1_delivery_address,
            cls.partner_br_stock_1,
            cls.so_line_product_1
            + cls.so_line_note
            + cls.so_line_section
            + cls.so_line_product_2,
        )

        cls.sale_order_br_5 = cls._create_br_sale_order(
            cls.partner_br_stock_1_delivery_address,
            cls.partner_br_stock_1_delivery_address,
            cls.partner_br_stock_1_delivery_address,
            cls.so_line_product_1
            + cls.so_line_note
            + cls.so_line_section
            + cls.so_line_product_2,
        )

    @classmethod
    def _create_br_sale_order(
        cls, partner, partner_shipping, partner_invoice, sale_order_lines
    ):
        """Create a Sale Order with the Brazilian Fiscal Operation (Venda).

        A Operação Fiscal, o dado adicional manual e a Operação Fiscal das
        linhas são os usados pelos testes do Wizard de faturamento do módulo.
        """
        fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        sale_order = create_with_form_sale_order(
            cls.env,
            cls.so_vals
            | {
                "partner_id": partner,
                "partner_shipping_id": partner_shipping,
                "partner_invoice_id": partner_invoice,
            },
            sale_order_lines,
        )
        sale_order.fiscal_operation_id = fiscal_operation
        sale_order.manual_customer_additional_data = "Manual Customer Additional Data"
        sale_order.manual_fiscal_additional_data = "Manual Fiscal Additional Data"
        for line in sale_order.order_line:
            line.fiscal_operation_id = fiscal_operation

        return sale_order
