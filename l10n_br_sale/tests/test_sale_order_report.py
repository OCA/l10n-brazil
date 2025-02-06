# Copyright (C) 2025-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestSaleReport(TestSaleCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner_a
        sale_form.pricelist_id = cls.company_data["default_pricelist"]
        sale_form.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        with sale_form.order_line.new() as line:
            line.name = cls.company_data["product_order_no"].name
            line.product_id = cls.company_data["product_order_no"]
            line.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
            line.fiscal_operation_line_id = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
            line.price_unit = cls.company_data["product_order_no"].list_price
            line.product_uom_qty = 3
        sale_form.save()

    def test_sale_br_report_sale_order(self):
        """Test Sale Report for Brazil Case"""
        self.env["sale.report"].read_group(
            domain=[],
            fields=["product_id, quantity, type_id"],
            groupby="fiscal_operation_id",
        )
