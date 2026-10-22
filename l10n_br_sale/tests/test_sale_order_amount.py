# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase
from odoo.tests.common import tagged


@tagged("post_install", "-at_install")
class TestSaleOrderAmount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        # FURN_8855 has IPI, a tax not included in the price
        cls.product = cls.env.ref("product.product_product_27")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")

    def test_amounts_of_order_created_on_server(self):
        """The order amounts take the taxes into account when the lines are
        created without the form view, as the blanket order wizard does"""
        operation_line = self.fiscal_operation.line_definition(
            self.company, self.partner, self.product
        )
        order = self.env["sale.order"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "fiscal_operation_id": self.fiscal_operation.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2.0,
                            "price_unit": 100.0,
                            "fiscal_operation_id": self.fiscal_operation.id,
                            "fiscal_operation_line_id": operation_line.id,
                        },
                    )
                ],
            }
        )
        line = order.order_line
        self.assertTrue(line.fiscal_amount_tax)
        self.assertEqual(line.price_tax, line.fiscal_amount_tax)
        self.assertEqual(line.price_total, line.fiscal_amount_total)
        self.assertEqual(order.amount_tax, line.fiscal_amount_tax)
        self.assertEqual(
            order.amount_total, order.amount_untaxed + line.fiscal_amount_tax
        )
