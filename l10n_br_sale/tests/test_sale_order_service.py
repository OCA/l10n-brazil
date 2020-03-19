# Copyright (C) 2016  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.tests import common


class TestSaleOrderService(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrderService, self).setUp()
        self.sale_order_service = self.env.ref(
            "l10n_br_sale.sale_order_service")

    def test_sale_order_service(self):
        """ Test Sale Order with service and product
            to check if create two invoices. """

        self.sale_order_service.onchange_partner_id()
        self.sale_order_service.onchange_partner_shipping_id()

        for line in self.sale_order_service.order_line:
            line._onchange_product_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()
            self.assertTrue(
                line.operation_id,
                "Error to mapping Operation on Sale Order Line.",
            )
            self.assertTrue(
                line.operation_line_id,
                "Error to mapping Operation Line on Sale Order Line.",
            )

        # Confirm sale order
        self.sale_order_service.action_confirm()

        # Create Invoice
        self.sale_order_service.action_invoice_create(final=True)

        # Verify if the two Invoices were created
        count_invoice = 0
        for order in self.sale_order_service.invoice_ids:
            count_invoice += 1
        self.assertTrue(count_invoice == 2)
