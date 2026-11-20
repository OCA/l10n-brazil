# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseOrderAmount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.service = cls.env["product.product"].search(
            [("type", "=", "service")], limit=1
        )

    def _create_order(self):
        return self.env["purchase.order"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "fiscal_operation_id": False,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.service.id,
                            "product_qty": 1.0,
                            "price_unit": 2000.0,
                        },
                    )
                ],
            }
        )

    def test_amounts_of_order_without_fiscal_operation(self):
        """The order without fiscal operation has the standard amounts, they
        are not taken from the order itself while it is being computed"""
        order = self._create_order()
        self.assertEqual(order.amount_untaxed, 2000.0)
        self.assertEqual(order.amount_total, 2000.0 + order.amount_tax)
        order.order_line.price_unit = 3000.0
        self.assertEqual(order.amount_untaxed, 3000.0)
        self.assertEqual(order.amount_total, 3000.0 + order.amount_tax)

    def test_amounts_of_copied_order_without_fiscal_operation(self):
        new_order = self._create_order().copy()
        self.assertEqual(new_order.amount_untaxed, 2000.0)
        self.assertEqual(new_order.amount_total, 2000.0 + new_order.amount_tax)
