# Copyright 2026 Engenere.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestSaleOrderCopy(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls.env.ref("l10n_br_sale.main_company-sale_2")

    def test_partner_order_is_not_copied(self):
        """A duplicated sale order is another order from the customer: like the
        customer reference of the order, the partner order of its lines is not
        copied."""
        self.sale_order.client_order_ref = "PO0042"
        self.sale_order.order_line.write(
            {"partner_order": "PO0042", "partner_order_line": "1"}
        )

        new_order = self.sale_order.copy()

        self.assertTrue(new_order.order_line)
        self.assertFalse(new_order.client_order_ref)
        self.assertFalse(any(new_order.order_line.mapped("partner_order")))
        self.assertFalse(any(new_order.order_line.mapped("partner_order_line")))
