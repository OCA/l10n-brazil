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

    def test_amounts_when_fiscal_amounts_are_read_first(self):
        """The line amounts follow the fiscal ones when these are read while
        the line is still to be recomputed, as the procurement does"""
        order = self.env["sale.order"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "fiscal_operation_id": self.fiscal_operation.id,
            }
        )
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "price_unit": 100.0,
                "fiscal_operation_id": self.fiscal_operation.id,
                "fiscal_operation_line_id": self.fiscal_operation.line_definition(
                    self.company, self.partner, self.product
                ).id,
            }
        )
        order.force_compute_delivery_costs_by_total = True
        order.amount_freight_value = 10.0
        line._prepare_br_fiscal_dict()
        self.assertEqual(line.fiscal_amount_untaxed, 110.0)
        self.assertEqual(line.price_subtotal, 110.0)
        self.assertEqual(order.amount_untaxed, 110.0)

    def _create_order_without_fiscal_operation(self):
        service = self.env["product.product"].search(
            [("type", "=", "service")], limit=1
        )
        order = self.env["sale.order"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "fiscal_operation_id": False,
                "order_line": [
                    (0, 0, {"display_type": "line_section", "name": "Section"}),
                    (0, 0, {"display_type": "line_note", "name": "Note"}),
                    (
                        0,
                        0,
                        {
                            "product_id": service.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 2000.0,
                        },
                    ),
                ],
            }
        )
        return order, order.order_line.filtered(lambda line: not line.display_type)

    def test_amounts_of_order_without_fiscal_operation(self):
        """The order without fiscal operation has the standard amounts, they
        are not taken from the order itself while it is being computed"""
        order, line = self._create_order_without_fiscal_operation()
        self.assertEqual(line.price_subtotal, 2000.0)
        self.assertEqual(order.amount_untaxed, 2000.0)
        self.assertEqual(order.amount_total, 2000.0)

        line.price_unit = 3000.0
        self.assertEqual(order.amount_untaxed, 3000.0)
        self.assertEqual(order.amount_total, 3000.0)

        # an old amount is not kept either
        self.env.cr.execute(
            "UPDATE sale_order SET amount_untaxed = 14400, amount_total = 14400"
            " WHERE id = %s",
            (order.id,),
        )
        order.invalidate_recordset()
        line.price_unit = 2000.0
        self.assertEqual(order.amount_untaxed, 2000.0)
        self.assertEqual(order.amount_total, 2000.0)

    def test_amounts_of_copied_order_without_fiscal_operation(self):
        order, _line = self._create_order_without_fiscal_operation()
        new_order = order.copy()
        self.assertEqual(new_order.amount_untaxed, 2000.0)
        self.assertEqual(new_order.amount_total, 2000.0)
